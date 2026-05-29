from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    role: str = "student"  # roles: student | teacher | admin
