# app_frontend.py (replace your current Streamlit file with this)
import time
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
from utils.api import (
    login, signup, upload_file, list_documents, delete_doc,
    rag_answer, extract_text, search_similarity, summarize, format_text,
    create_chat_session, list_chat_sessions, get_chat_messages, save_chat_message,
    update_chat_title, delete_chat_session, refresh_access
)

st.set_page_config(page_title="AI-Powered Document Intelligence Hub", layout="wide")

# -------------------------
# Session init
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "page" not in st.session_state:
    st.session_state.page = "login"   # login, documents, chat, ocr, summarize, format, search
if "chat" not in st.session_state:
    st.session_state.chat = []        # list of dicts {role, content, timestamp}
if "username" not in st.session_state:
    st.session_state.username = None
if "email" not in st.session_state:
    st.session_state.email = None
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# -------------------------
# Helper: show mode banner
# -------------------------
def show_mode_banner():
    mode = st.session_state.get("mode")
    username = st.session_state.get("username")
    email = st.session_state.get("email")
    if mode:
        st.markdown(
            f"""
            <div style="background-color:#F0FFF4;color:#4CAF50;padding:8px;border-radius:8px;
                        font-weight:500;font-size:12px;border:1px solid #d1fae5;margin-bottom:12px;">
                🟢 {html_lib.escape(mode)}
            </div>
            <div style="background-color:black;color:#1E90FF;padding:8px;border-radius:8px;
                        font-weight:500;font-size:12px;border:1px solid #d1ecff;margin-bottom:12px;">
                👤 Logged in as {html_lib.escape(username)} ({html_lib.escape(email)})
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------
# Token refresh + retry helper
# -------------------------
def _try_refresh_and_update():
    """
    Use st.session_state.refresh_token to call backend refresh endpoint.
    If successful, update st.session_state.token (and refresh_token if provided by backend).
    Returns True if refresh succeeded, False otherwise.
    """
    refresh_tok = st.session_state.get("refresh_token")
    if not refresh_tok:
        return False

    resp = refresh_access(refresh_tok)
    if resp is None:
        return False

    if resp.status_code == 200:
        data = resp.json()
        new_access = data.get("access_token")
        new_refresh = data.get("refresh_token")
        if new_access:
            st.session_state.token = new_access
        if new_refresh:
            st.session_state.refresh_token = new_refresh
        return True
    else:
        # Refresh failed — clear auth state
        st.session_state.token = None
        st.session_state.refresh_token = None
        st.session_state.mode = None
        st.session_state.username = None
        st.session_state.email = None
        return False

def call_with_refresh(func, *args, **kwargs):
    """
    Wrapper for calling utils.api functions which expect token as first positional arg.
    Usage:
      call_with_refresh(list_documents)
      call_with_refresh(upload_file, file_obj)
      call_with_refresh(get_chat_messages, session_id)
    Behavior:
      - Calls func(token, *args, **kwargs)
      - If response.status_code == 401, attempts refresh once and retries
      - Returns the response object (or None on internal failure)
    """
    token = st.session_state.get("token")
    try:
        resp = func(token, *args, **kwargs)
    except Exception as e:
        # Could not call function (network error etc.)
        return None

    # If unauthorized -> attempt refresh once
    try:
        status = getattr(resp, "status_code", None)
    except Exception:
        status = None

    if status == 401:
        refreshed = _try_refresh_and_update()
        if not refreshed:
            return resp  # still 401; let caller handle (usually show login)
        # retry once with updated token
        token = st.session_state.get("token")
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
                st.rerun()
            else:
                # debug info
                st.error("Unable to create session. Please log in again.")
                st.session_state.token = None
                st.session_state.refresh_token = None

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
                    st.rerun()

                # Delete button
                if col2.button("🗑️", key=f"del_chat_{s['id']}"):
                    delete_resp = call_with_refresh(delete_chat_session, s["id"])
                    if delete_resp and delete_resp.status_code == 200:
                        if "current_chat" in st.session_state and st.session_state.current_chat == s["id"]:
                            st.session_state.current_chat = None
                        st.rerun()
                    else:
                        st.error("Failed to delete chat session")

    st.sidebar.markdown("<div style='height:130px'></div>", unsafe_allow_html=True)

    with st.sidebar.container():
        show_mode_banner()
        if st.sidebar.button("Logout", key="nav_logout_btn"):
            do_logout()

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
            elif res.status_code == 200:
                data = res.json()
                st.session_state.token = data.get("access_token")
                st.session_state.refresh_token = data.get("refresh_token")  # store refresh token if returned
                st.session_state.mode = data.get("mode", "")
                st.session_state.username = data.get("username", "")
                st.session_state.email = data.get("email", "")
                st.success("Login successful!")
                st.session_state.page = "documents"
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
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
            elif res.status_code in (200, 201):
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
            if res and res.status_code == 200:
                st.success("Uploaded & indexed!")
            else:
                st.error(f"Upload failed: {getattr(res, 'text', res)}")

    # list documents
    st.subheader("Your Files")
    res = call_with_refresh(list_documents)
    if res and res.status_code == 200:
        docs = res.json().get("documents", [])
        for doc in docs:
            col1, col2 = st.columns([8, 2])
            col1.write(f"📄 {doc.get('filename')}")
            if col2.button("Delete", key=f"del_{doc.get('id')}"):
                r = call_with_refresh(delete_doc, doc.get("id"))
                if r and r.status_code == 200:
                    st.success("Deleted")
                else:
                    st.error("Delete failed")
                # refresh UI
                st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.experimental_set_query_params(reload=int(time.time()))
    else:
        # if token expired or unauthorized, prompt login
        if res and getattr(res, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            page_login()
        else:
            st.error("Failed to load documents")

# -------------------------
# Chat page
# -------------------------
def page_chat():
    sticky_title("💬 Chat")

    # If no chat selected, create one
    if "current_chat" not in st.session_state or st.session_state.current_chat is None:
        resp = call_with_refresh(create_chat_session)
        if resp and resp.status_code == 200:
            st.session_state.current_chat = resp.json()["session_id"]
        else:
            st.warning("Could not create chat session. Please login again.")
            return

    # Load messages
    resp = call_with_refresh(get_chat_messages, st.session_state.current_chat)
    if resp and resp.status_code == 200:
        messages = resp.json()
        st.session_state.chat = [
            {"role": m["role"], "content": m["content"], "timestamp": m["timestamp"]}
            for m in messages
        ]
    else:
        if resp and getattr(resp, "status_code", None) == 401:
            st.warning("Session expired — please login again.")
            page_login()
            return
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
        try:
            if len(st.session_state.chat) == 0:
                title = (msg.strip()[:80]) if msg else "New Chat"
                call_with_refresh(update_chat_title, st.session_state.current_chat, title)
        except Exception:
            pass

        # Save user message
        call_with_refresh(save_chat_message, st.session_state.current_chat, "user", msg)

        # Get AI reply
        with st.spinner("Thinking…"):
            response = call_with_refresh(rag_answer, msg)
            data = response.json() if (response and hasattr(response, "json")) else {}

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
    docs = res.json().get("documents", []) if (res and res.status_code == 200) else []
    doc_map = {d["filename"]: d["id"] for d in docs}
    choice = st.selectbox("Select file", list(doc_map.keys()))
    if st.button("Extract"):
        file_id = doc_map[choice]
        r = call_with_refresh(extract_text, file_id)
        if r and r.status_code == 200:
            st.text_area("Extracted Text", r.json().get("extracted_text",""), height=300)
        else:
            st.error("Extraction failed")

def page_summarize():
    sticky_title("📝 Summarize")
    text = st.text_area("Text to summarize", height=200)
    method = st.selectbox("Method", ["abstractive","extractive","bullet"])
    if st.button("Summarize"):
        r = call_with_refresh(summarize, text, method)
        if r and r.status_code==200:
            st.text_area("Summary", r.json().get("summary",""), height=200)
        else:
            st.error("Error summarizing")

def page_format():
    sticky_title(" Format Text")
    text = st.text_area("Text to format", height=200)
    fmt = st.selectbox("Format", ["markdown","json","table"])
    if st.button("Format"):
        r = call_with_refresh(format_text, text, fmt)
        if r and r.status_code==200:
            st.text_area("Formatted", r.json(), height=200)
        else:
            st.error("Formatting failed")

def page_search():
    sticky_title("🔎 Search Similar Documents")
    q = st.text_input("Query")
    top_k = st.text_input("Top K", "3")
    if st.button("Search"):
        r = call_with_refresh(search_similarity, q, top_k)
        if r and r.status_code==200:
            st.json(r.json())
        else:
            st.error("Search failed")

# -------------------------
# Logout
# -------------------------
def do_logout():
    st.session_state.token = None
    st.session_state.refresh_token = None
    st.session_state.mode = None
    st.session_state.chat = []
    st.session_state.page = "login"
    st.query_params = {"logout": int(time.time())}
    st.rerun()

# -------------------------
# Main render logic
# -------------------------
sidebar_nav()

if st.session_state.page == "login":
    page_login()
elif st.session_state.page == "documents":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_documents()
elif st.session_state.page == "chat":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_chat()
elif st.session_state.page == "ocr":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_ocr()
elif st.session_state.page == "summarize":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_summarize()
elif st.session_state.page == "format":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_format()
elif st.session_state.page == "search":
    if not st.session_state.token:
        st.warning("Please login to continue.")
        page_login()
    else:
        page_search()
elif st.session_state.page == "logout":
    do_logout()
else:
    st.info("Unknown page. Go to Login.")
