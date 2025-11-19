from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.db import get_db
from app.models.documents import Document
from app.services.ocr_service import extract_text
from app.models.users import User
from app.core.security import user_or_admin



router = APIRouter(prefix="/text", tags=["OCR & AUDIO"])


@router.post("/extract")
def ocr_extract(file_id: str, db: Session = Depends(get_db),current_user: User = Depends(user_or_admin)):
    """
    Extract text from a document using OCR or PDF text extraction.
    """
    #  Find file in database
    doc = db.query(Document).filter(Document.id == file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = doc.path

    #  Extract text using OCR / PDF logic
    result = extract_text(file_path)

    #  Handle failures
    if result.startswith("[") and result.endswith("]"):
        raise HTTPException(status_code=400, detail=result)

    return {
        "file_id": file_id,
        "filename": doc.filename,
        "extracted_text": result
    }
