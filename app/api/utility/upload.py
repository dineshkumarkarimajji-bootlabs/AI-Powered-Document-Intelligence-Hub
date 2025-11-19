from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.db import get_db
from app.models.users import User
from app.core.security import user_or_admin
from app.models.documents import Document
from app.common_utils.file_handler import save_upload
from app.services.retriever_service import Retriever


router = APIRouter(prefix="/upload", tags=["Upload"])
retriever = Retriever()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    # Check duplicate
    if db.query(Document).filter(Document.filename == file.filename).first():
        raise HTTPException(409, "File already exists")

    # Save uploaded file
    file_id, path, media_type = save_upload(file)

    # Save to DB
    doc = Document(
        id=file_id,
        filename=file.filename,
        path=path,
        media_type=media_type,
        owner=current_user.username,
        is_indexed=False,
        chunks_count=0
    )
    db.add(doc)
    db.commit()

    # Index in Chroma
    index_result = retriever.add_document(path, user=current_user.username, user_role=current_user.role)

    # Update PostgreSQL state
    doc.is_indexed = True
    doc.chunks_count = index_result["chunks"]
    db.commit()
    db.refresh(doc)

    return {
        "file_id": file_id,
        "indexed": True,
        "chunks": doc.chunks_count,
        "message": "File uploaded & indexed successfully"
    }
