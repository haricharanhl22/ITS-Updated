from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    role: str = "student"  # roles: student | teacher | admin
    auth_user_id: Optional[str] = None  # linked Supabase Auth user id (uuid), if any
