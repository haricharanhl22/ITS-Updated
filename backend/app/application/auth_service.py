from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings
from app.domain.user import User
from app.infrastructure.user_repository import (
    create_user,
    get_user_by_username,
    verify_password,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def _create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def authenticate_user(req: LoginRequest) -> TokenResponse:
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user.hashed_password):
        raise ValueError("Invalid username or password")
    if not user.is_active:
        raise ValueError("Account is disabled")

    token = _create_access_token(
        {"sub": user.username, "role": user.role, "id": user.id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


def register_user(req: RegisterRequest) -> TokenResponse:
    user = create_user(
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.role,
    )
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
from app.config.supabase_client import supabase


def register_user(email: str, password: str):

    response = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    return response


def login_user(email: str, password: str):

    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    return response