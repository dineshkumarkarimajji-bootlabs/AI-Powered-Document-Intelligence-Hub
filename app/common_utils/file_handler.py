import os
from pathlib import Path
import uuid
from app.core.config import settings
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.documents import Document
from app.services.vector_service import VectorStoreService

vector_service = VectorStoreService()

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)

def save_upload(file):
    ext = Path(file.filename).suffix
    file_id = uuid.uuid4().hex
    filepath = upload_dir / file.filename

    if filepath.exists():
        filepath = upload_dir / f"{file_id}_{file.filename}"

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return file_id, str(filepath), file.content_type




def delete_document_and_vectors(db: Session, doc_id: str, username: str):

    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if (document.owner != username):
        raise HTTPException(status_code=403, detail="Not allowed to delete this document")

    # 1. Delete vectors from vector DB
    vector_service.delete_by_doc_id(doc_id)
    path = document.path

    # 2. Delete file from local storage
    if os.path.exists(path):
        os.remove(path)

    # 3. Delete record from PostgreSQL
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}

