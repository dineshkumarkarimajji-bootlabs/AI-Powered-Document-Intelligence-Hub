from fastapi import APIRouter, Body
from app.services.retriever_service import Retriever
from app.models.users import User
from fastapi import Depends
from app.core.security import user_or_admin

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/similarity")
def search(query: str = Body(...), top_k: int = Body(3), current_user: User = Depends(user_or_admin)):
    retriever = Retriever()
    result = retriever.query(query, top_k=top_k, user_role=current_user.role)
    formatted = [
        {"document_id": doc["source"], "score": doc["score"]}
        for doc in result
    ]

    return {"results": formatted}
