from fastapi import APIRouter, Form, Depends
from app.models.users import User
from app.core.security import user_or_admin
from app.schemas.summarize_schema import SummaryMethod
from app.services.summarization import summarizer

router = APIRouter(prefix="/summarize", tags=["Summarization"])

@router.post("/text")
def summarize_text(
    text: str = Form(...),
    method: SummaryMethod = Form(SummaryMethod.abstractive),
    current_user: User = Depends(user_or_admin)
):
    result = summarizer.summarize(text, method.value)
    return {"summary": result}
