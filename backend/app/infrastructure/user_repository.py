"""
User repository — backed by Supabase Postgres.
All user data is stored in the public.users table.
"""
import hashlib
import hmac
import os

from app.config.supabase_client import supabase
from app.domain.user import User

_ITERATIONS = 260_000
_SALT_SIZE = 16


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    salt = os.urandom(_SALT_SIZE)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return salt.hex() + ":" + key.hex()


def _verify_password(plain: str, stored: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash."""
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, _ITERATIONS)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        hashed_password=row["hashed_password"],
        role=row["role"],
        is_active=row.get("is_active", True),
        is_verified=row.get("is_verified", False),
    )


def get_user_by_username(username: str) -> User | None:
    result = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
    )
    if result.data:
        return _row_to_user(result.data[0])
    return None


def get_user_by_email(email: str) -> User | None:
    result = (
        supabase.table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    if result.data:
        return _row_to_user(result.data[0])
    return None


def create_user(username: str, email: str, password: str, role: str = "student") -> User:
    # Check for duplicates before inserting
    if get_user_by_username(username):
        raise ValueError(f"Username '{username}' already exists")
    if get_user_by_email(email):
        raise ValueError(f"Email '{email}' already registered")

    hashed = _hash_password(password)
    result = (
        supabase.table("users")
        .insert({
            "username": username,
            "email": email,
            "hashed_password": hashed,
            "role": role,
            "is_active": True,
            "is_verified": False,
        })
        .execute()
    )
    return _row_to_user(result.data[0])


def mark_user_verified(email: str) -> None:
    """Set is_verified=True for the user with this email."""
    supabase.table("users").update({"is_verified": True}).eq("email", email).execute()


def is_user_verified(email: str) -> bool:
    """Return True if the user's email has been verified."""
    result = (
        supabase.table("users")
        .select("is_verified")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0].get("is_verified", False)
    return False


def verify_password(plain: str, hashed: str) -> bool:
    return _verify_password(plain, hashed)
