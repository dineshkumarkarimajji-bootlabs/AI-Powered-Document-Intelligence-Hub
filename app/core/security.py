from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import users as model
from app.models.db import get_db
import uuid
import hashlib

# -------------------- JWT CONFIG --------------------
SECRET_KEY = "45a70544539124673fc8daf946a53a71b72daed29d8e5cf451bd669a40d3b390"
REFRESH_SECRET_KEY="b1c3e8f4d5e6a7b8901234567890abcdef1234567890abcdef1234567890abcd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 14

# -------------------- Password Context --------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# -------------------- Refresh Token Helpers --------------------
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def verify_refresh_token(token: str, hashed: str) -> bool:
    return hashlib.sha256(token.encode()).hexdigest() == hashed

# -------------------- ACCESS TOKEN --------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    if "sub" not in to_encode:
        to_encode["sub"] = data.get("email")

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------- REFRESH TOKEN --------------------
def create_refresh_token(data: dict):
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": jti})

    token = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token, "jti": jti}

# -------------------- OAUTH2 --------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
    ):
    # Try Authorization header token first
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(model.User).filter(
        model.User.email == email,
        model.User.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# -------------------- ROLE CHECKS --------------------
def admin_required(current_user: model.User = Depends(get_current_user)):
    if current_user.role != model.Roles.ADMIN:
        raise HTTPException(403, "Admin privileges required")
    return current_user

def user_or_admin(current_user: model.User = Depends(get_current_user)):
    if current_user.role not in [
        model.Roles.Student, model.Roles.Doctor, model.Roles.Business_Man,
        model.Roles.Financer, model.Roles.Lawyer, model.Roles.ADMIN
    ]:
        raise HTTPException(403, "User or Admin privileges required")
    return current_user
