import time
import html as html_lib
import streamlit as st
import streamlit.components.v1 as components
from utils.api import login, signup, upload_file, list_documents, delete_doc, rag_answer, extract_text, search_similarity, summarize, format_text

st.set_page_config(page_title="AI-Powered Document Intelligence Hub", layout="wide")

# -------------------------
# Session init
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "page" not in st.session_state:
    st.session_state.page = "login"   # login, documents, chat, ocr, summarize, format, search
if "chat" not in st.session_state:
    st.session_state.chat = []        # list of (role, text, iso_ts)
if "username" not in st.session_state:
    st.session_state.username = None
if "email" not in st.session_state:
    st.session_state.email = None

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
def sidebar_nav():
    st.sidebar.title("Docs AI")

    # ---- Updated CSS (Streamlit 1.30+ compatible) ----
    st.sidebar.markdown("""
        <style>
            /* Sidebar container spacing */
            section[data-testid="stSidebar"] {
                padding-top: 5px !important;
                margin-top: 0px !important;
                margin-bottom: 0px !important;
            }

            /* Make all sidebar buttons same width & height */
            section[data-testid="stSidebar"] button {
                width: 200px !important;
                height: 40px !important;
                border-radius: 10px !important;
                font-size: 12px !important;
                display: flex;
                justify-content: start;
                align-items: center;
            }

            /* Optional: Highlight selected page */
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

    # ---- Render Navigation Buttons ----
    for label, value in pages.items():
        if st.sidebar.button(label, key=f"nav_{value}"):
            st.session_state.page = value
            st.rerun()

    # ---- Space before bottom logout ----
    st.sidebar.markdown("<div style='height:160px'></div>", unsafe_allow_html=True)

    # ---- Logout Section ----
    with st.sidebar.container():
        show_mode_banner()
        st.markdown(
            '<div style="position: absolute; bottom: 10px; width: 90%;">',
            unsafe_allow_html=True
        )
        if st.sidebar.button("Logout", key="nav_logout_btn"):
            do_logout()
        st.markdown('</div>', unsafe_allow_html=True)

    

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
            if res.status_code == 200:
                data = res.json()
                st.session_state.token = data["access_token"]
                st.session_state.mode = data.get("mode", "")
                st.session_state.username = data.get("username", "")
                st.session_state.email = data.get("email", "")
                st.success("Login successful!")
                # move to documents after login
                st.session_state.page = "documents"

                # Force rerun after login
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
            else:
                st.error(res.json().get("detail", "Login failed"))

    with tab2:
        username = st.text_input("Username", key="signup_username")
        email2 = st.text_input("Email", key="signup_email")
        password2 = st.text_input("Password", type="password", key="signup_password")
        role = st.selectbox("Role", ["Student", "doctor", "lawyer", "business_man", "financer", "admin"], key="signup_role")
        if st.button("Create Account", key="signup_btn"):
            res = signup(username, email2, password2, role)
            if res.status_code in (200, 201):
                st.success("Signup successful — now login.")
            else:
                st.error(res.json().get("detail", "Signup failed"))

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
            res = upload_file(st.session_state.token, file)
            if res.status_code == 200:
                st.success("Uploaded & indexed!")
            else:
                st.error(f"Upload failed: {res.text}")

    # list documents
    st.subheader("Your Files")
    res = list_documents(st.session_state.token)
    if res.status_code == 200:
        docs = res.json().get("documents", [])
        for doc in docs:
            col1, col2 = st.columns([8, 2])
            col1.write(f"📄 {doc.get('filename')}")
            if col2.button("Delete", key=f"del_{doc.get('id')}"):
                r = delete_doc(st.session_state.token, doc.get("id"))
                if r.status_code == 200:
                    st.success("Deleted")
                else:
                    st.error("Delete failed")
                st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.experimental_set_query_params(reload=int(time.time()))
    else:
        st.error("Failed to load documents")

def page_chat():
    sticky_title("💬 Chat")

    # Init chat storage
    if "chat" not in st.session_state:
        st.session_state.chat = []     # list of (role, msg, ts)

    # --------------------- CHAT HISTORY (TOP) ---------------------
    def render_chat():
        css = """
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
        </style>
        """

        html = css + "<div id='chatbox' class='chatbox'>"

        for role, text, ts in st.session_state.chat:
            safe = html_lib.escape(text)
            if role == "assistant":
                html += f"""
                <div class="msg-row msg-left">
                    <div>
                        <div class="meta">{ts} • AI</div>
                        <div class="bubble-left">{safe}</div>
                    </div>
                </div>
                """
            else:
                html += f"""
                <div class="msg-row msg-right">
                    <div>
                        <div class="meta" style="text-align:right;">{ts} • You</div>
                        <div class="bubble-right">{safe}</div>
                    </div>
                </div>
                """

        html += """
        </div>
        <script>
            var box = document.getElementById("chatbox");
            if (box) { box.scrollTop = box.scrollHeight; }
        </script>
        """
        return html

    components.html(render_chat(), height=580, scrolling=False)

    # --------------------- USER INPUT (BOTTOM) using a form ---------------------
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([9, 1])
        with cols[0]:
            user_query = st.text_input("Message", placeholder="Type your message…", key="msg_box")
        with cols[1]:
            send = st.form_submit_button("Send")

    # --------------------- WHEN FORM IS SUBMITTED ---------------------
    if send and user_query and user_query.strip():
        msg = user_query.strip()

        # store user message
        st.session_state.chat.append(("user", msg, time.strftime("%H:%M:%S")))

        # call backend
        with st.spinner("Thinking…"):
            try:
                r = rag_answer(st.session_state.token, msg)
                answer = r.json().get("answer", "No response")
            except Exception as e:
                answer = f"[Error] {e}"

        # store assistant message
        st.session_state.chat.append(("assistant", answer, time.strftime("%H:%M:%S")))

        # rerun to render updated chat (input cleared by form automatically)
        st.rerun()


# -------------------------
# OCR / Summarize / Format / Search pages (simple)
# -------------------------
def page_ocr():
    sticky_title("🖹 OCR / Extract Text")
    res = list_documents(st.session_state.token)
    docs = res.json().get("documents", []) if res.status_code==200 else []
    doc_map = {d["filename"]: d["id"] for d in docs}
    choice = st.selectbox("Select file", list(doc_map.keys()))
    if st.button("Extract"):
        file_id = doc_map[choice]
        r = extract_text(st.session_state.token, file_id)
        if r.status_code == 200:
            st.text_area("Extracted Text", r.json().get("extracted_text",""), height=300)
        else:
            st.error("Extraction failed")

def page_summarize():
    sticky_title("📝 Summarize")
    text = st.text_area("Text to summarize", height=200)
    method = st.selectbox("Method", ["abstractive","extractive","bullet"])
    if st.button("Summarize"):
        r = summarize(st.session_state.token, text, method)
        if r.status_code==200:
            st.text_area("Summary", r.json().get("summary",""), height=200)
        else:
            st.error("Error summarizing")

def page_format():
    sticky_title(" Format Text")
    text = st.text_area("Text to format", height=200)
    fmt = st.selectbox("Format", ["markdown","json","table"])
    if st.button("Format"):
        r = format_text(st.session_state.token, text, fmt)
        if r.status_code==200:
            st.text_area("Formatted", r.json(), height=200)
        else:
            st.error("Formatting failed")

def page_search():
    sticky_title("🔎 Search Similar Documents")
    q = st.text_input("Query")
    top_k = st.text_input("Top K", "3")
    if st.button("Search"):
        r = search_similarity(st.session_state.token, q, top_k)
        if r.status_code==200:
            st.json(r.json())
        else:
            st.error("Search failed")

# -------------------------
# Logout
# -------------------------
def do_logout():
    st.session_state.token = None
    st.session_state.mode = None
    st.session_state.chat = []
    st.session_state.page = "login"

    # NEW SYNTAX (Streamlit 1.30+)
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
