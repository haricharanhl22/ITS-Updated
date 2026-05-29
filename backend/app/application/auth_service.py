from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.application.email_service import send_otp_email
from app.config.settings import settings
from app.domain.user import User
from app.infrastructure.otp_repository import create_otp, verify_otp
from app.infrastructure.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    mark_user_verified,
    verify_password,
)
from app.schemas.auth import LoginRequest, OtpVerifyRequest, RegisterRequest, TokenResponse


def _create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def authenticate_user(req: LoginRequest) -> TokenResponse:
    # Accept username OR email
    user = get_user_by_username(req.username) or get_user_by_email(req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise ValueError("Invalid username or password")
    if not user.is_active:
        raise ValueError("Account is disabled")
    if not user.is_verified:
        raise ValueError("Please verify your email before logging in")

    token = _create_access_token(
        {"sub": user.username, "role": user.role, "id": user.id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


def register_user(req: RegisterRequest) -> dict:
    """Create user (unverified) and send OTP email. Returns email for OTP step."""
    user = create_user(
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.role,
    )
    otp = create_otp(user.email)
    send_otp_email(user.email, otp)
    return {"message": "OTP sent to your email. Please verify to continue.", "email": user.email}


def verify_otp_and_login(req: OtpVerifyRequest) -> TokenResponse:
    """Verify OTP, mark user as verified, and return JWT token."""
    if not verify_otp(req.email, req.otp):
        raise ValueError("Invalid or expired OTP")

    mark_user_verified(req.email)

    user = get_user_by_email(req.email)
    if not user:
        raise ValueError("User not found")

    token = _create_access_token(
        {"sub": user.username, "role": user.role, "id": user.id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise ValueError("Token is invalid or expired")


def get_current_user_from_token(token: str) -> User:
    payload = decode_token(token)
    username: str = payload.get("sub")
    if not username:
        raise ValueError("Token missing subject")
    user = get_user_by_username(username)
    if not user:
        raise ValueError("User not found")
    return user