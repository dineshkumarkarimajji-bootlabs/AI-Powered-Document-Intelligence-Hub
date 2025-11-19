from fastapi import APIRouter, Query
from app.services.rag_service import ask_llm
from app.services.retriever_service import Retriever
from app.models.users import User
from fastapi import Depends
from app.core.security import user_or_admin
import time


router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/answer")
def answer(query: str=Query(...), top_k: int = 7, use_llm: bool = True, current_user: User = Depends(user_or_admin)):
    start_time = time.time()
    retriever = Retriever()
    result = retriever.query(query, top_k=top_k, user=current_user.username, user_role=current_user.role)
    answer = ask_llm(query, [r["text"] for r in result], current_user) if use_llm else "LLM not used"
    elapsed = time.time() - start_time
    if not use_llm:
        answer = result[0]["text"] if result else "No relevant documents found."
    return {"query": query, "results": result, "answer": answer, "metrics": retriever.evaluate(query, result), "query_time_sec": round(elapsed, 2)}

