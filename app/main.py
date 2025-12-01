from fastapi import FastAPI
from app.api.routes import router
from app.models.db import Base, engine


from app.models.users import User
from app.models.documents import Document
from app.models.user_chart import  ChatMessage  
from app.models.user_chart import  ChatSession  

app = FastAPI(title="Document AI Hub", version="1.0.0")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

app.include_router(router)
