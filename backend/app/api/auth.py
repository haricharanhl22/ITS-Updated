from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.application.auth_service import (
    authenticate_user,
    get_current_user_from_token,
    register_user,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return get_current_user_from_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── JSON login (used by frontend fetch/axios) ──────────────────────────────
@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    try:
        return authenticate_user(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ── OAuth2 form login (used by Swagger UI) ─────────────────────────────────
@router.post("/auth/token", response_model=TokenResponse)
def token(form: OAuth2PasswordRequestForm = Depends()):
    req = LoginRequest(username=form.username, password=form.password)
    try:
        return authenticate_user(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ── Register ───────────────────────────────────────────────────────────────
@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest):
    try:
        return register_user(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ── Get current user ───────────────────────────────────────────────────────
@router.get("/auth/me", response_model=UserOut)
def me(current_user=Depends(_get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
    )


# ── Logout (client-side token discard; endpoint for audit logging) ─────────
@router.post("/auth/logout")
def logout(current_user=Depends(_get_current_user)):
    # JWT is stateless — actual invalidation happens on the client by removing the token.
    # Extend here with a token blacklist if needed.
    return {"message": f"User '{current_user.username}' logged out successfully"}
