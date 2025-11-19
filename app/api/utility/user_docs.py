from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common_utils.file_handler import delete_document_and_vectors
from app.models.db import get_db
from app.models.documents import Document
from app.core.security import user_or_admin
from app.models.users import User
from app.services.vector_service import VectorStoreService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/")
def get_user_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    docs = db.query(Document).filter(Document.owner == current_user.username).all()
    return {"documents": docs}




@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    db = Depends(get_db),
    current_user: User = Depends(user_or_admin),
    # vector_service: VectorStoreService = Depends()
):
    return delete_document_and_vectors(
        db=db,
        # vector_service=vector_service,     
        doc_id=doc_id,
        username=current_user.username,
    )
