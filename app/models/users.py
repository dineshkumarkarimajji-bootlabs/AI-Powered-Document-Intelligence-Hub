from sqlalchemy import Column, Integer, String, DateTime,Boolean
from datetime import datetime
from app.models.db import Base
from enum import Enum as pyEnum

class Roles(str, pyEnum):
    ADMIN="admin"
    Lawyer="lawyer"
    Doctor="doctor"
    Business_Man="business_man"
    Financer="financer"
    Student="student"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=Roles.Student.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

