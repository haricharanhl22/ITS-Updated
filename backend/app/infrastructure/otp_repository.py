"""
OTP token repository — stores and verifies one-time passwords in Supabase.
"""
import random
import string
from datetime import datetime, timedelta, timezone

from app.config.supabase_client import supabase

_OTP_EXPIRY_MINUTES = 10


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def create_otp(email: str) -> str:
    """Generate a 6-digit OTP, persist it, and return the code."""
    otp = _generate_otp()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=_OTP_EXPIRY_MINUTES)
    ).isoformat()

    # Invalidate any previous unused OTPs for this email
    supabase.table("otp_tokens").update({"used": True}).eq("email", email).eq(
        "used", False
    ).execute()

    supabase.table("otp_tokens").insert(
        {
            "email": email,
            "otp": otp,
            "expires_at": expires_at,
            "used": False,
        }
    ).execute()

    return otp


def verify_otp(email: str, otp: str) -> bool:
    """
    Return True if the OTP is valid for this email (correct, not used, not expired).
    Marks the token as used on success.
    """
    now = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("otp_tokens")
        .select("id")
        .eq("email", email)
        .eq("otp", otp)
        .eq("used", False)
        .gt("expires_at", now)
        .limit(1)
        .execute()
    )

    if not result.data:
        return False

    token_id = result.data[0]["id"]
    supabase.table("otp_tokens").update({"used": True}).eq("id", token_id).execute()
    return True
