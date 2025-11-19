from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.models.db import get_db
from app.models.users import User
from app.core.security import hash_password, verify_password, create_access_token
from app.models.users import Roles
from fastapi import Form

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- SIGNUP ---
@router.post("/signup")
def signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: Roles = Form(Roles.Student),
    db: Session = Depends(get_db)
):
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="User already exists")

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

# --- LOGIN ---

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    if user.role =="doctor":
        mode="Healthcare Mode Activated"
    elif user.role =="lawyer":
        mode="Legal Mode Activated"
    elif user.role =="business_man":
        mode="Business Mode Activated"
    elif user.role =="financer":
        mode="Finance Mode Activated"
    elif user.role =="admin":
        mode="Admin Mode Activated"
    else:
        mode="Student Mode Activated"

    token = create_access_token({"sub": user.email})

    return {"access_token": token, "token_type": "bearer", "mode": mode,"username": user.username,
    "email": user.email}





