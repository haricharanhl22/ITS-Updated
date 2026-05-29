from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.application.auth_service import (
    authenticate_user,
    get_current_user_from_token,
    register_user,
    verify_otp_and_login,
)
from app.schemas.auth import (
    LoginRequest,
    OtpVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserOut,
)

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


# ── Register → sends OTP, does NOT return a token yet ─────────────────────
@router.post("/auth/register", response_model=RegisterResponse, status_code=201)
def register(req: RegisterRequest):
    try:
        return register_user(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ── Verify OTP → marks user verified + returns JWT ─────────────────────────
@router.post("/auth/verify-otp", response_model=TokenResponse)
def verify_otp(req: OtpVerifyRequest):
    try:
        return verify_otp_and_login(req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Get current user ───────────────────────────────────────────────────────
@router.get("/auth/me", response_model=UserOut)
def me(current_user=Depends(_get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


# ── Logout ─────────────────────────────────────────────────────────────────
@router.post("/auth/logout")
def logout(current_user=Depends(_get_current_user)):
    return {"message": f"User '{current_user.username}' logged out successfully"}
