from sqlalchemy import Column, String, DateTime, Integer, Boolean
from datetime import datetime
from app.models.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, unique=True)
    path = Column(String)
    media_type = Column(String)
    owner = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_indexed = Column(Boolean, default=False)
    chunks_count = Column(Integer, default=0)
    
