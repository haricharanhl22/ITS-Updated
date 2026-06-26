"""
backend/app/api/chat.py
FastAPI router — POST /chat/ask and GET /chat/messages/{student_id}

CHANGED: All endpoints are async/await. Calls async tutor_service.get_answer()
         and async chat_repository.get_recent_messages(). student_id accepted as
         str in the path/body and passed through to service layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.auth.auth_service import get_current_student
from app.application.tutor_service import get_answer
from app.infrastructure import chat_repository

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Request / Response models ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question:   str


class AskResponse(BaseModel):
    answer:           str
    concept_detected: str


class ChatMessageOut(BaseModel):
    id:         int
    role:       str
    content:    str
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
async def ask(
    req: AskRequest,
    student_id: str = Depends(get_current_student),
):
    """
    Ask the AI tutor a Python question.
    - Detects the concept via keyword matching (stub phase).
    - Persists both user message and assistant reply to the messages table.
    - Returns answer + concept_detected so the sidebar can highlight the concept.
    """
    if not req.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty.",
        )

    try:
        result = await get_answer(
            question=req.question.strip(),
            student_id=student_id,
        )
        return AskResponse(
            answer=result["answer"],
            concept_detected=result["concept_detected"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tutor error: {e}",
        )


@router.get("/messages", response_model=list[ChatMessageOut])
async def get_messages(
    student_id: str = Depends(get_current_student),
):
    """
    Return the last 10 messages for a student in chronological order.
    Hard-capped at 10 to protect LLM context windows.
    """
    rows = await chat_repository.get_recent_messages(student_id, limit=10)
    return [
        ChatMessageOut(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            created_at=str(r.get("created_at", "")),
        )
        for r in rows
    ]
