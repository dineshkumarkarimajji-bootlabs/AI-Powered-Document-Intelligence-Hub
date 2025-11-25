from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.db import get_db
from app.models.users import User
from app.core.security import user_or_admin
from app.models.user_chart import ChatMessage, ChatSession

router = APIRouter(prefix="/chat", tags=["Chat History"])

@router.post("/session/create")
async def create_session(db: Session = Depends(get_db), current_user: User = Depends(user_or_admin)):
    session = ChatSession(user_id=current_user.id, title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id}


from pydantic import BaseModel

class MessagePayload(BaseModel):
    role: str
    content: str

@router.post("/chat/session/{session_id}/message")
def add_message(
    session_id: int,
    body: MessagePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    msg = ChatMessage(
        session_id=session_id,
        role=body.role,
        content=body.content,
    )
    db.add(msg)
    db.commit()
    return {"status": "saved"}


@router.get("/chat/sessions")
async def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(user_or_admin)):
    sessions = db.query(ChatSession)\
                 .filter(ChatSession.user_id == current_user.id)\
                 .order_by(ChatSession.created_at.desc())\
                 .all()

    return [{"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions]

@router.get("/chat/session/{session_id}/messages")
async def get_messages(session_id: int,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(user_or_admin)):

    messages = db.query(ChatMessage)\
                 .filter(ChatMessage.session_id == session_id)\
                 .order_by(ChatMessage.timestamp.asc())\
                 .all()

    return [{
        "role": m.role,
        "content": m.content,
        "timestamp": m.timestamp
    } for m in messages]


from pydantic import BaseModel

class TitleUpdate(BaseModel):
    title: str

@router.put("/chat/session/{session_id}/title")
async def update_chat_title(
    session_id: int,
    body: TitleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        return {"detail": "Session not found"}

    session.title = body.title
    db.commit()

    return {"status": "updated"}

@router.delete("/chat/session/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_or_admin)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        return {"detail": "Session not found"}

    # Delete all messages first
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()

    db.delete(session)
    db.commit()

    return {"status": "deleted"}



