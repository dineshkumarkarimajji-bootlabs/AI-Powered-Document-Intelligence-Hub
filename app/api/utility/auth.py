from fastapi import APIRouter, HTTPException, Depends, Form, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.models.db import get_db
from app.models.users import User, Roles
from app.core.security import (
    REFRESH_SECRET_KEY,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token, SECRET_KEY, ALGORITHM,
    hash_refresh_token,
    verify_refresh_token
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
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
    ):
    # Find user
    user = db.query(User).filter(User.email == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Mode selection
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
    refresh = create_refresh_token({"sub": user.email})  # {"token": "...", "jti": "..."}

    refresh_token = refresh["token"]
    refresh_jti = refresh["jti"]

    # Store hashed refresh token
    user.refresh_token_hash = hash_refresh_token(refresh_token)
    user.refresh_jti = refresh_jti
    db.commit()

    # OPTIONAL: Set cookies (browser won't see them from Streamlit)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 30,
        samesite="lax",
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 14,
        samesite="lax",
        path="/"
    )

    # --------------------------
    # !!! MOST IMPORTANT PART !!!
    # --------------------------
    # THIS is what your frontend expects
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "mode": mode,
        "username": user.username,
        "email": user.email
    }



@router.post("/refresh")
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """
    Accepts either form-encoded or JSON with {"refresh_token": "..."}.
    Returns 400 if no refresh token provided.
    """

    refresh_token = None

    # Try reading form data (multipart or x-www-form-urlencoded)
    try:
        form = await request.form()
        refresh_token = form.get("refresh_token") or form.get("refreshToken")
    except Exception:
        pass

    # Try reading JSON body
    if not refresh_token:
        try:
            body = await request.json()
            if isinstance(body, dict):
                refresh_token = body.get("refresh_token") or body.get("refreshToken")
        except Exception:
            pass

    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token missing in request")

    # Verify refresh token
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Fetch user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate stored hashed refresh token
    if not verify_refresh_token(refresh_token, user.refresh_token_hash) or jti != user.refresh_jti:
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    # Create new tokens
    new_access = create_access_token({"sub": email})
    new_refresh_obj = create_refresh_token({"sub": email})

    new_refresh = new_refresh_obj["token"]
    new_jti = new_refresh_obj["jti"]

    # Store new hashed refresh token
    user.refresh_token_hash = hash_refresh_token(new_refresh)
    user.refresh_jti = new_jti
    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }
