from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.db import get_db
from app.models.documents import Document
from app.services.ocr_service import extract_text
from app.models.users import User
from app.core.security import user_or_admin


router = APIRouter(prefix="/text", tags=["OCR & AUDIO"])


@router.post("/extract")
async def ocr_extract(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    """
    Extract text from uploaded documents (PDF, DOCX, Image, Audio, etc.)
    """


    doc: Document = db.query(Document).filter(Document.id == file_id).first()

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {file_id} not found"
        )

    file_path = doc.path  
    print("DEBUG FILE PATH =>", file_path)  

    import os
    ext = os.path.splitext(file_path)[1].lower()
    if not ext:
        raise HTTPException(
            status_code=400,
            detail="File has no extension. Cannot detect extractor."
        )

    try:
        result = extract_text(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR extraction failed: {str(e)}"
        )


    if result.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="No text extracted from document"
        )

    if result.startswith("[") and result.endswith("]"):
        raise HTTPException(status_code=400, detail=result)


    return {
        "file_id": file_id,
        "filename": doc.filename,
        "extension": ext,
        "extracted_text": result
    }
