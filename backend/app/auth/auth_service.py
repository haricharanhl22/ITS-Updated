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
            auth_id = res.user.id
            if email:
                from app.infrastructure.user_repository import (
                    get_user_by_auth_id, get_user_by_email, get_user_by_username,
                    create_user, set_auth_user_id, delete_user, mark_user_verified,
                )
                # Resolve identity by the stable Supabase Auth id first — email
                # alone is not a safe key, since deleting a Supabase Auth user
                # and re-registering with the same email issues a brand-new
                # auth id but would otherwise still match the OLD `users` row
                # by email, silently resurrecting its old mastery/history onto
                # what should be a fresh account.
                db_user = get_user_by_auth_id(auth_id)
                if not db_user:
                    existing_by_email = get_user_by_email(email)
                    if existing_by_email and not existing_by_email.auth_user_id:
                        # Legacy row created before this linkage existed —
                        # adopt it once, preserving its history.
                        set_auth_user_id(existing_by_email.id, auth_id)
                        db_user = existing_by_email
                    elif existing_by_email:
                        # This email belonged to a DIFFERENT, now-superseded
                        # Supabase Auth account. Treat this as a genuinely new
                        # signup: drop the stale row (cascades to wipe its
                        # mastery/events/etc.) and create a fresh one.
                        delete_user(existing_by_email.id)

                    if not db_user:
                        username = email.split("@")[0]
                        if get_user_by_username(username):
                            username = f"{username}_{auth_id[:8]}"
                        db_user = create_user(
                            username=username,
                            email=email,
                            password="",
                            role="student",
                            auth_user_id=auth_id,
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
