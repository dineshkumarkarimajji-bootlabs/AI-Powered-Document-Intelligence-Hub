from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import users as model
from app.models.db import get_db

# -------------------- JWT CONFIG --------------------
SECRET_KEY = "45a70544539124673fc8daf946a53a71b72daed29d8e5cf451bd669a40d3b390"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# -------------------- Password Context --------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# -------------------- Hashing Password --------------------
def hash_password(password: str) -> str:
    # Truncate if longer than 72 bytes
    return pwd_context.hash(password)


# -------------------- Verifying Password --------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify the provided plain password against the hashed password.
    return pwd_context.verify(plain_password, hashed_password)

# -------------------- TOKEN CREATION --------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    if "sub" not in to_encode and "email" in to_encode:
        to_encode["sub"] = to_encode["email"]
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -------------------- OAUTH2 SCHEME --------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -------------------- CURRENT USER --------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        role: str = payload.get("role", "USER")
        user_id: int = payload.get("id")
    except JWTError:
        raise credentials_exception

    user = db.query(model.User).filter(model.User.email == email, model.User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user

# -------------------- ROLE-BASED AUTH --------------------
def admin_required(current_user: model.User = Depends(get_current_user)):
    if current_user.role != model.Roles.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

def user_or_admin(current_user: model.User = Depends(get_current_user)):
    if current_user.role not in [model.Roles.Student, model.Roles.Doctor, model.Roles.Business_Man, model.Roles.Financer,model.Roles.Lawyer, model.Roles.ADMIN]:
        raise HTTPException(status_code=403, detail="User or Admin privileges required")
    return current_user


