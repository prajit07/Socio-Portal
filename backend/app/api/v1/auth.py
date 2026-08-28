from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import RegisterIn, TokenOut, UserOut
from app.services import otp_service

logger = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class OtpRequest(BaseModel):
    email: EmailStr
    purpose: str = "verify"  # register | verify | login


class OtpVerify(BaseModel):
    email: EmailStr
    code: str
    purpose: str = "verify"


class LoginCodeRequest(BaseModel):
    email: EmailStr
    password: str


class LoginVerify(BaseModel):
    email: EmailStr
    code: str


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        phone=payload.phone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email address to continue.",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenOut(access_token=token)


@router.post("/request-otp")
def request_otp(payload: OtpRequest, db: Session = Depends(get_db)):
    logger.info("request-otp email=%s purpose=%s", payload.email, payload.purpose)
    dev_code = otp_service.request_otp(db, payload.email, payload.purpose, channel="email")
    return {"detail": "otp_sent", "channel": "email", "dev_code": dev_code}


@router.post("/verify-otp")
def verify_otp(payload: OtpVerify, db: Session = Depends(get_db)):
    ok = otp_service.verify_otp(db, payload.email, payload.code, payload.purpose)
    if not ok:
        logger.warning("verify-otp FAILED email=%s purpose=%s", payload.email, payload.purpose)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    user = db.query(User).filter(User.email == payload.email).first()
    if user and payload.purpose in ("register", "verify"):
        user.is_email_verified = True
        db.commit()
    logger.info("verify-otp OK email=%s purpose=%s", payload.email, payload.purpose)
    return {"detail": "verified", "email_verified": True}


@router.post("/login/request-code")
def login_request_code(payload: LoginCodeRequest, db: Session = Depends(get_db)):
    """Step 1 of OTP-gated login: verify credentials, then email a login code."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("login/request-code FAILED (bad credentials) email=%s", payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    dev_code = otp_service.request_otp(db, payload.email, "login", channel="email")
    logger.info("login/request-code OK email=%s", payload.email)
    return {"detail": "otp_sent", "channel": "email", "dev_code": dev_code}


@router.post("/login/verify", response_model=TokenOut)
def login_verify(payload: LoginVerify, db: Session = Depends(get_db)):
    """Step 2 of OTP-gated login: verify the code, then issue the JWT."""
    ok = otp_service.verify_otp(db, payload.email, payload.code, "login")
    if not ok:
        logger.warning("login/verify FAILED email=%s", payload.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    user = db.query(User).filter(User.email == payload.email).first()
    if user and not user.is_email_verified:
        user.is_email_verified = True
        db.commit()
    token = create_access_token(subject=str(user.id), role=user.role.value)
    logger.info("login/verify OK email=%s role=%s", payload.email, user.role.value if user else "unknown")
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
