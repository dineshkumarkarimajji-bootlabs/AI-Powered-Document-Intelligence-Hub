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
