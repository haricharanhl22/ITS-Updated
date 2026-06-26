from fastapi import Header, HTTPException, status

from app.config.settings import settings


def get_current_student(authorization: str = Header(...)) -> str:
    """
    FastAPI dependency to extract and verify the JWT.

    Supports two token formats in priority order:
    1. Custom HS256 JWT (issued by /auth/login and /demo/login).
       Payload contains {"sub": username, "id": student_db_id, "role": ...}
       Returns the numeric student id (as a string).

    2. Supabase Auth JWT (issued by Supabase directly).
       Falls back to supabase.auth.get_user() for Supabase-issued tokens.
       Returns the Supabase user UUID.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]

    # ── Attempt 1: Custom HS256 JWT ──────────────────────────────────────────
    try:
        from jose import JWTError, jwt as jose_jwt
        payload = jose_jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        # Prefer the numeric DB id over the username for mastery lookups
        student_id = payload.get("id") or payload.get("sub")
        if student_id is not None:
            return str(student_id)
    except Exception:
        pass  # Not a valid custom JWT — try Supabase next

    # ── Attempt 2: Supabase Auth JWT ─────────────────────────────────────────
    try:
        from app.config.supabase_client import supabase
        res = supabase.auth.get_user(token)
        if res and res.user:
            email = res.user.email
            if email:
                from app.infrastructure.user_repository import get_user_by_email, create_user, get_user_by_username, mark_user_verified
                db_user = get_user_by_email(email)
                if not db_user:
                    username = email.split("@")[0]
                    if get_user_by_username(username):
                        username = f"{username}_{res.user.id[:8]}"
                    db_user = create_user(
                        username=username,
                        email=email,
                        password="",
                        role="student",
                    )
                    mark_user_verified(email)
                return str(db_user.id)
            return str(res.user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
