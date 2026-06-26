"""
backend/app/api/demo.py
POST /demo/login — returns a short-lived JWT for a demo persona.
No real auth — persona switcher is the entry point for the demo.

Personas seeded by seed_personas.py:
  ava_beginner   → low mastery
  marcus_inter   → medium mastery  
  priya_advanced → high mastery
"""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.auth_service import authenticate_user
from app.schemas.auth import LoginRequest

router = APIRouter(prefix="/demo", tags=["demo"])

# Hardcoded demo credentials (set by seed_personas.py)
PERSONAS: dict[str, dict] = {
    "beginner": {
        "username": "ava_beginner",
        "password": "DemoPass123!",
        "display_name": "Ava",
        "level": "beginner",
        "emoji": "🌱",
        "tagline": "Just getting started",
    },
    "intermediate": {
        "username": "marcus_inter",
        "password": "DemoPass123!",
        "display_name": "Marcus",
        "level": "intermediate",
        "emoji": "📚",
        "tagline": "Building solid skills",
    },
    "advanced": {
        "username": "priya_advanced",
        "password": "DemoPass123!",
        "display_name": "Priya",
        "level": "advanced",
        "emoji": "🔥",
        "tagline": "Pushing the limits",
    },
}


class DemoLoginRequest(BaseModel):
    persona: str   # "beginner" | "intermediate" | "advanced"


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type:   str
    username:     str
    display_name: str
    level:        str
    emoji:        str
    tagline:      str
    student_id:   int


@router.post("/login", response_model=DemoLoginResponse)
async def demo_login(req: DemoLoginRequest):
    persona_key = req.persona.lower()
    if persona_key not in PERSONAS:
        raise HTTPException(status_code=400, detail=f"Unknown persona '{req.persona}'. Use: beginner, intermediate, advanced")

    persona = PERSONAS[persona_key]
    try:
        login_req = LoginRequest(username=persona["username"], password=persona["password"])
        token_data = await asyncio.to_thread(authenticate_user, login_req)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Demo persona '{persona_key}' is not seeded. Run: python seed_personas.py. Error: {e}",
        )

    # Fetch the student's database ID
    from app.infrastructure.user_repository import get_user_by_username
    user = await asyncio.to_thread(get_user_by_username, persona["username"])
    if not user:
        raise HTTPException(status_code=500, detail="Demo persona user not found in database.")

    return DemoLoginResponse(
        access_token=token_data.access_token,
        token_type=token_data.token_type,
        username=user.username,
        display_name=persona["display_name"],
        level=persona["level"],
        emoji=persona["emoji"],
        tagline=persona["tagline"],
        student_id=user.id,
    )


@router.get("/personas")
async def list_personas():
    """Return the persona metadata for the entry screen (no auth needed)."""
    return [
        {k: v for k, v in p.items() if k != "password"}
        for p in PERSONAS.values()
    ]
