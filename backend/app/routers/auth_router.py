from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import SignupRequest, LoginRequest, TokenResponse
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user_name=user.name, user_id=user.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user_name=user.name, user_id=user.id)
