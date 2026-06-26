"""
backend/app/api/learning_events.py
GET /api/learning-events/{student_id} — returns mastery history for sparklines.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.auth.auth_service import get_current_student
from app.config.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["learning_events"])

class LearningEvent(BaseModel):
    id:            int
    concept_name:  str
    score:         float
    created_at:    str


def _fetch_events(student_id: str, limit: int) -> list[dict]:
    result = (
        supabase.table("learning_events")
        .select("id, concept_name, score, created_at")
        .eq("student_id", student_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


@router.get("/learning-events", response_model=list[LearningEvent])
async def get_learning_events(
    limit: int = 50,
    student_id: str = Depends(get_current_student),
):
    events = await asyncio.to_thread(_fetch_events, student_id, min(limit, 100))
    return [
        LearningEvent(
            id=e["id"],
            concept_name=e["concept_name"],
            score=float(e.get("score") or 0.0),
            created_at=str(e.get("created_at") or ""),
        )
        for e in events
    ]
