from fastapi import APIRouter, Form, Depends
from sqlalchemy import Enum
from app.models.users import User
from app.core.security import user_or_admin
from app.common_utils.formatter import format_response
from app.schemas.formate_schema import FormatMethod

router = APIRouter(prefix="/format", tags=["Text Formatting"])


@router.post("/text")
async def format_text_endpoint(
    text: str = Form(...),
    format: FormatMethod = Form(FormatMethod.markdown),
    user: User = Depends(user_or_admin)
):
    return format_response(text, format)