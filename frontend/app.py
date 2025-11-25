import time
import html as html_lib
import os
import streamlit as st
import streamlit.components.v1 as components
from streamlit_cookies_manager import EncryptedCookieManager

from utils.api import (
    login, signup, upload_file, list_documents, delete_doc,
    rag_answer, extract_text, search_similarity, summarize, format_text,
    create_chat_session, list_chat_sessions, get_chat_messages, save_chat_message,
    update_chat_title, delete_chat_session, refresh_access
)

st.set_page_config(page_title="AI-Powered Document Intelligence Hub", layout="wide")

# -------------------------
# Cookie manager (browser-persistent)
# -------------------------
# Use a strong password in production: set ST_COOKIE_PASSWORD env var or use st.secrets
COOKIES_PASSWORD = os.environ.get("ST_COOKIE_PASSWORD", "dev-secret-change-me")
cookies = EncryptedCookieManager(prefix="auth_", password=COOKIES_PASSWORD)

# Wait for cookie manager handshake with browser
if not cookies.ready():
    st.stop()

# -------------------------
# Session init & Token Sync (Optimized for robustness)
# -------------------------

# Load tokens and user data from cookies
cookie_access = cookies.get("access_token")
cookie_refresh = cookies.get("refresh_token")
cookie_page = cookies.get("last_page")

# 1. Initialize ALL required session state keys to prevent KeyErrors/AttributeErrors
if "token" not in st.session_state:
    st.session_state.token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "username" not in st.session_state:
    st.session_state.username = None
if "email" not in st.session_state:
    st.session_state.email = None
if "page" not in st.session_state:
    st.session_state.page = None
if "chat" not in st.session_state:
    st.session_state.chat = []
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


# 2. Synchronize Session State with Cookies (overwrites None defaults)
st.session_state.token = cookie_access if cookie_access else st.session_state.token
st.session_state.refresh_token = cookie_refresh if cookie_refresh else st.session_state.refresh_token
st.session_state.mode = cookies.get("mode")
st.session_state.username = cookies.get("username")
st.session_state.email = cookies.get("email")


# 3. Set page default/restore last page
if st.session_state.page is None or st.session_state.page == "login":
    valid_pages = ["documents", "chat", "ocr", "summarize", "format", "search"]
    
    if st.session_state.token and cookie_page in valid_pages:
        st.session_state.page = cookie_page
    elif st.session_state.token:
        st.session_state.page = "documents"
    else:
        st.session_state.page = "login"

# -------------------------
# Helper: Logout function (must be defined early)
# -------------------------
def do_logout(reset_page=True):
    # Clear session state
    st.session_state.token = None
    st.session_state.refresh_token = None
    st.session_state.mode = None
    st.session_state.chat = []
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.current_chat = None
    if reset_page:
        st.session_state.page = "login"

    # delete cookies
    cookies["access_token"] = ""
    cookies["refresh_token"] = ""
    cookies["mode"] = ""
    cookies["username"] = ""
    cookies["email"] = ""
    cookies["last_page"] = "login"
    cookies.save()

    # force UI update
    if reset_page:
        st.rerun()

# -------------------------
# Helper: show mode banner
# -------------------------
def show_mode_banner():
    mode = st.session_state.mode
    username = st.session_state.username
    email = st.session_state.email
    if mode:
        st.markdown(
            f"""
            <div style="background-color:#F0FFF4;color:#4CAF50;padding:8px;border-radius:8px;
                        font-weight:500;font-size:12px;border:1px solid #d1fae5;margin-bottom:12px;">
                🟢 {html_lib.escape(mode)}
            </div>
            <div style="background-color:black;color:#1E90FF;padding:8px;border-radius:8px;
                        font-weight:500;font-size:12px;border:1px solid #d1ecff;margin-bottom:12px;">
                👤 Logged in as {html_lib.escape(username or '')} ({html_lib.escape(email or '')})
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------
# Token refresh + retry helper
# -------------------------
def _try_refresh_and_update():
    """
    Use cookie-stored refresh token to call backend refresh endpoint.
    Update cookies & session_state on success.
    """
    refresh_tok = st.session_state.refresh_token
    if not refresh_tok:
        return False

    try:
        resp = refresh_access(refresh_tok)
    except Exception:
        return False

    if resp is None:
        return False

    if getattr(resp, "status_code", None) == 200:
        data = resp.json()
        new_access = data.get("access_token")
        new_refresh = data.get("refresh_token")

        # update cookies if provided and mirror to session_state
        if new_access:
            cookies["access_token"] = new_access
            st.session_state.token = new_access
        if new_refresh:
            cookies["refresh_token"] = new_refresh
            st.session_state.refresh_token = new_refresh
        cookies.save()
        return True
    else:
        # Refresh failed — clear auth state
        do_logout(reset_page=False) # Only clear tokens, let router handle page change
        return False

def call_with_refresh(func, *args, **kwargs):
    """
    Wrapper for calling utils.api functions which expect token as first positional arg.
    """
    token = st.session_state.token
    if not token:
        # If no token, return None and let caller handle lack of auth
        return None

    # Attempt the call
    try:
        resp = func(token, *args, **kwargs)
    except Exception:
        return None

    status = getattr(resp, "status_code", None)

    # If unauthorized -> attempt refresh once
    if status == 401:
        refreshed = _try_refresh_and_update()
        if not refreshed:
            return resp  # still 401; let caller handle (usually show login)
        
        # retry once with updated token
        token = st.session_state.token
        try:
            resp = func(token, *args, **kwargs)
        except Exception:
            return None
            
    return resp

# -------------------------
def sidebar_nav():
    st.sidebar.title("Docs AI")

    # ---- Updated CSS (Streamlit 1.30+ compatible) ----
    st.sidebar.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                padding-top: 5px !important;
                margin-top: 0px !important;
                margin-bottom: 0px !important;
            }
            section[data-testid="stSidebar"] button {
                width: 200px !important;
                height: 40px !important;
                border-radius: 10px !important;
                font-size: 12px !important;
                display: flex;
                justify-content: start;
                align-items: center;
            }
            .selected-btn {
                background-color: #2d5dff !important;
                color: white !important;
                border: 1px solid #2d5dff !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # ---- Navigation Pages ----
    pages = {
        "Documents": "documents",
        "Chat": "chat",
        "Text Extraction": "ocr",
        "Summarize": "summarize",
        "Format": "format",
        "Search": "search",
    }

    for label, value in pages.items():
        if st.sidebar.button(label, key=f"nav_{value}"):
            st.session_state.page = value
            cookies["last_page"] = value
            cookies.save()
            st.rerun()
    
    # ---- Chat History Section ----
    if st.session_state.token:
        st.sidebar.subheader("💬 Chat History")

        # New chat button
        if st.sidebar.button("➕ New Chat", key="new_chat_btn"):
            resp = call_with_refresh(create_chat_session)
            if resp and resp.status_code == 200:
                st.session_state.current_chat = resp.json()["session_id"]
                st.session_state.page = "chat"
                cookies["last_page"] = "chat"
                cookies.save()
                st.rerun()
            else:
                st.error("Unable to create session. Please log in again.")
                # Force token reset if API call failed
                do_logout(reset_page=True)


        # Load sessions
        resp = call_with_refresh(list_chat_sessions)
        if resp and resp.status_code == 200:
            sessions = resp.json()
            # limit to latest 4 chats
            sessions = sessions[:4]
            for s in sessions:
                col1, col2 = st.sidebar.columns([4, 1])

                # Select chat
                if col1.button(f" {s['title']}", key=f"chat_{s['id']}"):
                    st.session_state.current_chat = s["id"]
                    st.session_state.page = "chat"
                    cookies["last_page"] = "chat"
                    cookies.save()
                    st.rerun()

                # Delete button
                if col2.button("🗑️", key=f"del_chat_{s['id']}"):
                    delete_resp = call_with_refresh(delete_chat_session, s["id"])
                    if delete_resp and delete_resp.status_code == 200:
                        if st.session_state.current_chat == s["id"]:
                            st.session_state.current_chat = None
                        st.rerun()
                    else:
                        st.error("Failed to delete chat session")
        elif resp and getattr(resp, "status_code", None) == 401:
            st.error("Session expired. Please log in again.")
            do_logout(reset_page=True)


    st.sidebar.markdown("<div style='height:130px'></div>", unsafe_allow_html=True)

    with st.sidebar.container():
        show_mode_banner()
        if st.sidebar.button("Logout", key="nav_logout_btn"):
            do_logout(reset_page=True)

# -------------------------
def sticky_title(title_text):
    st.markdown(
        f"""
        <style>
        .fixed-header {{
            position: sticky;
            top: 0;
            background: rgb(14, 17, 23);
            padding: 15px 0px 10px 0px;
            z-index: 999;
            border-bottom: 1px solid #e0e0e0;
        }}
        </style>

        <div class="fixed-header">
            <h2>{title_text}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------
# Chat Session Management Logic (NEW/UPDATED)
# -------------------------
def get_or_create_chat_session():
    """
    Attempts to reuse the last empty session, otherwise creates a new one.
    Sets st.session_state.current_chat on success.
    Returns True if a session is successfully set, False otherwise.
    """
    
    # 1. If we already have a session set, assume it's valid for this run.
    if st.session_state.current_chat is not None:
        return True

    # 2. Check the user's existing sessions
    list_resp = call_with_refresh(list_chat_sessions)

    if list_resp and getattr(list_resp, "status_code", None) == 200:
        sessions = list_resp.json()
        if sessions:
            # The list is already ordered by created_at.desc() by the backend
            last_session = sessions[0]
            last_session_id = last_session["id"]

            # 3. Check if the last session is empty
            messages_resp = call_with_refresh(get_chat_messages, last_session_id)
            
            if messages_resp and getattr(messages_resp, "status_code", None) == 200:
                messages = messages_resp.json()
                
                # If the last session has 0 messages, reuse it
                if len(messages) == 0:
                    st.session_state.current_chat = last_session_id
                    # Ensure page/cookie state reflects "chat"
                    st.session_state.page = "chat"
                    cookies["last_page"] = "chat"
                    cookies.save()
                    return True
                
    # 4. If no sessions exist, or the last one is not empty, create a new session
    resp = call_with_refresh(create_chat_session)
    if resp and getattr(resp, "status_code", None) == 200:
        session_id = resp.json()["session_id"]
        st.session_state.current_chat = session_id
        st.session_state.page = "chat"
        cookies["last_page"] = "chat"
        cookies.save()
        return True
    
    # 5. Handle authentication failure or other creation errors
    if list_resp and getattr(list_resp, "status_code", None) == 401 or \
       resp and getattr(resp, "status_code", None) == 401:
        st.warning("Session expired — please login again.")
        st.session_state.page = "login"
        st.rerun() 
        return False

    st.error("Could not load or create chat session.")
    return False

# -------------------------
# Login / Signup UI
# -------------------------
def page_login():
    sticky_title("Login / Signup")

    tab1, tab2 = st.tabs(["Login", "Signup"])
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            res = login(email, password)
            if res is None:
                st.error("Login request failed (network error).")
            elif getattr(res, "status_code", None) == 200:
                data = res.json()
                access = data.get("access_token")
                refresh = data.get("refresh_token")
                mode = data.get("mode", "")
                username = data.get("username", "")
                email_val = data.get("email", "")

                # store in cookies (persisted in browser)
                if access:
                    cookies["access_token"] = access
                if refresh:
                    cookies["refresh_token"] = refresh
                cookies["mode"] = mode
                cookies["username"] = username
                cookies["email"] = email_val
                cookies["last_page"] = "documents" # Set default page after successful login
                cookies.save()

                # mirror to session_state for immediate UI use
                st.session_state.token = access
                st.session_state.refresh_token = refresh
                st.session_state.mode = mode
                st.session_state.username = username
                st.session_state.email = email_val
                st.session_state.page = "documents"

                st.success("Login successful!")
                st.rerun()
            else:
                try:
                    st.error(res.json().get("detail", "Login failed"))
                except Exception:
                    st.error("Login failed")

    with tab2:
        username = st.text_input("Username", key="signup_username")
        email2 = st.text_input("Email", key="signup_email")
        password2 = st.text_input("Password", type="password", key="signup_password")
        role = st.selectbox("Role", ["Student", "doctor", "lawyer", "business_man", "financer", "admin"], key="signup_role")
        if st.button("Create Account", key="signup_btn"):
            res = signup(username, email2, password2, role)
            if res is None:
                st.error("Signup request failed (network error).")
            elif getattr(res, "status_code", None) in (200, 201):
                st.success("Signup successful — now login.")
            else:
                try:
                    st.error(res.json().get("detail", "Signup failed"))
                except Exception:
                    st.error("Signup failed")

# -------------------------
# Documents page (upload/list/delete)
# -------------------------
def page_documents():
    sticky_title("📁 Documents")

    # upload
    allowed_formats = ["pdf", "txt", "rtf", "png", "jpg", "jpeg", "mp3", "wav", "m4a", "mp4", "aac"]
    file = st.file_uploader("Upload a file", type=allowed_formats)
    if file is not None:
        if st.button("Upload"):
            res = call_with_refresh(upload_file, file)
            if res and getattr(res, "status_code", None) == 200:
                st.success("Uploaded & indexed!")
                st.rerun()
            elif res and getattr(res, "status_code", None) == 401:
                st.warning("Session expired — please login again.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(f"Upload failed: {getattr(res, 'text', res)}")

    # list documents
    st.subheader("Your Files")
    res = call_with_refresh(list_documents)
    if res and getattr(res, "status_code", None) == 200:
        docs = res.json().get("documents", [])
        for doc in docs:
            col1, col2 = st.columns([8, 2])
            col1.write(f"📄 {doc.get('filename')}")
            if col2.button("Delete", key=f"del_{doc.get('id')}"):
                r = call_with_refresh(delete_doc, doc.get('id'))
                if r and getattr(r, "status_code", None) == 200:
                    st.success("Deleted")
                elif r and getattr(r, "status_code", None) == 401:
                    st.warning("Session expired — please login again.")
                    st.session_state.page = "login"
                else:
                    st.error("Delete failed")
                st.rerun()
    elif res and getattr(res, "status_code", None) == 401:
        st.warning("Session expired — please login again.")
        st.session_state.page = "login"
        st.rerun()
    else:
        st.error("Failed to load documents")

# -------------------------
# Chat page
# -------------------------
def page_chat():
    sticky_title("💬 Chat")

    # 1. Get or create current chat session
    if not get_or_create_chat_session():
        # If the helper failed (e.g., token expired, already handled rerun)
        return

    # 2. Load messages
    resp = call_with_refresh(get_chat_messages, st.session_state.current_chat)
    if resp and getattr(resp, "status_code", None) == 200:
        messages = resp.json()
        st.session_state.chat = [
            {"role": m["role"], "content": m["content"], "timestamp": m["timestamp"]}
            for m in messages
        ]
    elif resp and getattr(resp, "status_code", None) == 401:
        st.warning("Session expired — please login again.")
        st.session_state.page = "login"
        st.rerun()
        return
    else:
        st.error("Failed to load chat messages")
        return

    # ---------------- CHAT UI ----------------
    CHAT_CSS = """
    <style>
    .chatbox {
        height: 540px;
        overflow-y: auto;
        padding: 15px;
        background: black;
        border-radius: 10px;
        border: 1px solid #222;
    }
    /* ... rest of CHAT_CSS ... (omitted for brevity) */
    .msg-row { display: flex; margin: 8px 0; width: 100%; }
    .msg-left  { justify-content: flex-start; }
    .msg-right { justify-content: flex-end; }
    .bubble-left {
        background: #f1f1f1;
        color: #111;
        padding: 12px;
        max-width: 75%;
        border-radius: 12px;
        border-bottom-left-radius: 4px;
        white-space: pre-wrap;
    }
    .bubble-right {
        background: #0b7bdc;
        color: white;
        padding: 12px;
        max-width: 75%;
        border-radius: 12px;
        border-bottom-right-radius: 4px;
        white-space: pre-wrap;
    }
    .meta {
        font-size: 11px;
        color: #9aa0a6;
        margin-bottom: 3px;
    }
    .metric-line {
        font-size: 11px;
        color: #00FFAA;
        margin-top: 3px;
    }
    </style>
    """

    def render_chat():
        html = CHAT_CSS + "<div id='chatbox' class='chatbox'>"
        for msg in st.session_state.chat:
            role = msg["role"]
            text = msg["content"]
            ts = msg["timestamp"]

            metric_display = ""
            if "📊 Answer Metrics" in text:
                parts = text.split("📊")
                main_txt = parts[0]
                metric_txt = "📊" + parts[1]
                safe_main = html_lib.escape(main_txt)
                metric_display = f"<div class='metric-line'>{html_lib.escape(metric_txt)}</div>"
            else:
                safe_main = html_lib.escape(text)

            if role == "assistant":
                html += f"""
                <div class="msg-row msg-left">
                    <div>
                        <div class="meta">{ts} • AI</div>
                        <div class="bubble-left">{safe_main}</div>
                        {metric_display}
                    </div>
                </div>
                """
            else:
                html += f"""
                <div class="msg-row msg-right">
                    <div>
                        <div class="meta" style="text-align:right;">{ts} • You</div>
                        <div class="bubble-right">{safe_main}</div>
                    </div>
                </div>
                """
        html += "</div>"
        return html

    components.html(render_chat(), height=580, scrolling=False)

    # ---------------- INPUT BOX ----------------
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([9, 1])
        user_query = cols[0].text_input("Message", placeholder="Type your message…", key="msg_box")
        send = cols[1].form_submit_button("Send")

    if send and user_query and user_query.strip():
        msg = user_query.strip()

        # Update chat title for first message
        if not st.session_state.chat:
            title = (msg.strip()[:80]) if msg else "New Chat"
            call_with_refresh(update_chat_title, st.session_state.current_chat, title)

        # Save user message
        call_with_refresh(save_chat_message, st.session_state.current_chat, "user", msg)

        # Get AI reply
        with st.spinner("Thinking…"):
            response = call_with_refresh(rag_answer, msg)
            data = response.json() if (response and hasattr(response, "json")) else {}

        if response and getattr(response, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            st.session_state.page = "login"
            st.rerun()
            return

        answer = data.get("answer", "No response")
        metrics = data.get("metrics", {})
        avg_sim = metrics.get("avg_similarity")
        hall_rate = metrics.get("hallucination_rate")

        metrics_text = ""
        if avg_sim is not None and hall_rate is not None:
            metrics_text = f"\n\n📊 Answer Metrics-: Avg Similarity: {avg_sim:.3f},Hallucination Rate: {hall_rate:.3f}"

        final_answer = answer + metrics_text

        # Save AI message
        call_with_refresh(save_chat_message, st.session_state.current_chat, "assistant", final_answer)

        st.rerun()

# -------------------------
# OCR / Summarize / Format / Search pages (simple)
# -------------------------
def page_ocr():
    sticky_title("OCR / Extract Text")
    res = call_with_refresh(list_documents)
    docs = res.json().get("documents", []) if (res and getattr(res, "status_code", None) == 200) else []
    
    if res and getattr(res, "status_code", None) == 401:
        st.warning("Session expired — please login again.")
        st.session_state.page = "login"
        st.rerun()
        return

    doc_map = {d["filename"]: d["id"] for d in docs}
    choice = st.selectbox("Select file", list(doc_map.keys()))
    if not doc_map:
        st.info("No documents uploaded yet.")
        return
        
    if st.button("Extract"):
        file_id = doc_map[choice]
        r = call_with_refresh(extract_text, file_id)
        if r and getattr(r, "status_code", None) == 200:
            st.text_area("Extracted Text", r.json().get("extracted_text",""), height=300)
        elif r and getattr(r, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Extraction failed")

def page_summarize():
    sticky_title("📝 Summarize")
    text = st.text_area("Text to summarize", height=200)
    method = st.selectbox("Method", ["abstractive","extractive","bullet"])
    if st.button("Summarize"):
        r = call_with_refresh(summarize, text, method)
        if r and getattr(r, "status_code", None) == 200:
            st.text_area("Summary", r.json().get("summary",""), height=200)
        elif r and getattr(r, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Error summarizing")

def page_format():
    sticky_title(" Format Text")
    text = st.text_area("Text to format", height=200)
    fmt = st.selectbox("Format", ["markdown","json","table"])
    if st.button("Format"):
        r = call_with_refresh(format_text, text, fmt)
        if r and getattr(r, "status_code", None) == 200:
            st.text_area("Formatted", r.json(), height=200)
        elif r and getattr(r, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Formatting failed")

def page_search():
    sticky_title("🔎 Search Similar Documents")
    q = st.text_input("Query")
    top_k = st.text_input("Top K", "3")
    if st.button("Search"):
        r = call_with_refresh(search_similarity, q, top_k)
        if r and getattr(r, "status_code", None) == 200:
            st.json(r.json())
        elif r and getattr(r, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Search failed")

# -------------------------
# Authentication Check (simplified)
# -------------------------
def ensure_logged_in():
    if not st.session_state.token:
        st.warning("Session required. Please login.")
        st.session_state.page = "login"
        st.rerun() # Use rerun to exit the current page function and go to router

# -------------------------
# Main render logic
# -------------------------

# Initial check for refresh token on startup if access token is missing
if not st.session_state.token and st.session_state.refresh_token:
    _try_refresh_and_update()

sidebar_nav()

# -----------------------------------------
# ROUTING
# -----------------------------------------

current_page = st.session_state.page

if current_page == "login":
    page_login()

elif current_page == "documents":
    ensure_logged_in()
    page_documents()

elif current_page == "chat":
    ensure_logged_in()
    page_chat()

elif current_page == "ocr":
    ensure_logged_in()
    page_ocr()

elif current_page == "summarize":
    ensure_logged_in()
    page_summarize()

elif current_page == "format":
    ensure_logged_in()
    page_format()

elif current_page == "search":
    ensure_logged_in()
    page_search()

elif current_page == "logout":
    do_logout(reset_page=True)

else:
    st.info("Unknown page. Please login.")
    st.session_state.page = "login"
    st.rerun()