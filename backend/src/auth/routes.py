from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.hash import hash_password, verify_password
from src.auth.jwt import create_access_token
from src.auth.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from src.db.session import get_db
from src.auth.deps import get_current_user
from src.models.user import User


router = APIRouter()


@router.post("/api/v1/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/api/v1/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {"sub": user.id, "role": user.role}
    access_token = create_access_token(token_data, expires_delta=timedelta(minutes=15))
    return TokenOut(access_token=access_token, expires_in=15)


@router.get("/api/v1/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
