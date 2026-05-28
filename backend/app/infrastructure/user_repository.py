"""
In-memory user repository (replace with a real DB later).
Stores a dict of username -> User.
"""
from passlib.context import CryptContext

from app.domain.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Seed users (in production, replace with DB queries)
_USERS: dict[str, User] = {
    "admin": User(
        id=1,
        username="admin",
        email="admin@hcai.edu",
        hashed_password=pwd_context.hash("admin123"),
        role="admin",
    ),
    "teacher": User(
        id=2,
        username="teacher",
        email="teacher@hcai.edu",
        hashed_password=pwd_context.hash("teacher123"),
        role="teacher",
    ),
    "student": User(
        id=3,
        username="student",
        email="student@hcai.edu",
        hashed_password=pwd_context.hash("student123"),
        role="student",
    ),
}

_next_id = 4


def get_user_by_username(username: str) -> User | None:
    return _USERS.get(username)


def get_user_by_email(email: str) -> User | None:
    for user in _USERS.values():
        if user.email == email:
            return user
    return None


def create_user(username: str, email: str, password: str, role: str = "student") -> User:
    global _next_id
    if username in _USERS:
        raise ValueError(f"Username '{username}' already exists")
    if get_user_by_email(email):
        raise ValueError(f"Email '{email}' already registered")
    user = User(
        id=_next_id,
        username=username,
        email=email,
        hashed_password=pwd_context.hash(password),
        role=role,
    )
    _USERS[username] = user
    _next_id += 1
    return user


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
