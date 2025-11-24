from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.models.db import get_db
from app.models.users import User, Roles
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token, SECRET_KEY, ALGORITHM
)
from jose import jwt, JWTError


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/signup")
async def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: Roles = Form(Roles.Student),
    db: Session = Depends(get_db)
):
    # Check if email or username exists
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Email or username already taken")

    hashed = hash_password(password)

    user = User(
        username=username,
        email=email,
        hashed_password=hashed,
        role=role.value
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully!"}


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Username is email
    user = db.query(User).filter(User.email == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Select Mode
    role_mode_map = {
        "doctor": "Healthcare Mode Activated",
        "lawyer": "Legal Mode Activated",
        "business_man": "Business Mode Activated",
        "financer": "Finance Mode Activated",
        "admin": "Admin Mode Activated",
    }

    mode = role_mode_map.get(user.role, "Student Mode Activated")

    # Create Tokens
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    # Store refresh token in DB
    user.refresh_token = refresh_token
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "mode": mode,
        "username": user.username,
        "email": user.email,
    }


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if refresh token is stored for any user
    user = db.query(User).filter(User.refresh_token == refresh_token).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Validate JWT refresh token
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")

    # Issue new access token
    new_access_token = create_access_token({"sub": email})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
