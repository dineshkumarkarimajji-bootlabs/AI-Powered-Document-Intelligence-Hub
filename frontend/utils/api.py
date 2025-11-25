import requests

BASE_URL = "http://localhost:8000"  # change if needed

def signup(username, email, password, role):
    data = {"username": username, "email": email, "password": password, "role": role}
    return requests.post(f"{BASE_URL}/auth/signup", data=data)

def login(email, password):
    data = {"username": email, "password": password}
    return requests.post(f"{BASE_URL}/auth/login", data=data)

def upload_file(token, file):
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": file}
    return requests.post(f"{BASE_URL}/upload/file", headers=headers, files=files)

def list_documents(token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(f"{BASE_URL}/documents/", headers=headers)

def delete_doc(token, doc_id):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=headers)

def rag_answer(token, query):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(f"{BASE_URL}/rag/answer?query={query}", headers=headers)

def search_similarity(token, query, top_k=3):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"query": query, "top_k": top_k}
    return requests.post(f"{BASE_URL}/search/similarity", headers=headers, json=data)

def extract_text(token, file_id):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(f"{BASE_URL}/text/extract?file_id={file_id}", headers=headers)

def summarize(token, text, method):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": text, "method": method}
    return requests.post(f"{BASE_URL}/summarize/text", headers=headers, data=data)

def format_text(token, text, fmt):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": text, "format": fmt}
    return requests.post(f"{BASE_URL}/format/text", headers=headers, data=data)


def create_chat_session(token):
    return requests.post(
        f"{BASE_URL}/chat/session/create",
        headers={"Authorization": f"Bearer {token}"}
    )

def list_chat_sessions(token):
    return requests.get(
        f"{BASE_URL}/chat/chat/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )

def get_chat_messages(token, session_id):
    return requests.get(
        f"{BASE_URL}/chat/chat/session/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )

def save_chat_message(token, session_id, role, content):
    return requests.post(
        f"{BASE_URL}/chat/chat/session/{session_id}/message",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"role": role, "content": content}   # MUST SEND JSON
    )

def update_chat_title(token, session_id, title):
    return requests.put(
        f"{BASE_URL}/chat/chat/session/{session_id}/title",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"title": title}
    )
def delete_chat_session(token, session_id):
    return requests.delete(
        f"{BASE_URL}/chat/chat/session/{session_id}",
        headers={"Authorization": f"Bearer {token}"}
    )


def refresh_access(refresh_token: str):
    # backend expects form field named refresh_token
    url = f"{BASE_URL}/auth/refresh"
    try:
        resp = requests.post(url, data={"refresh_token": refresh_token}, timeout=10)
        return resp
    except Exception as e:
        # make sure caller can handle failures
        return None