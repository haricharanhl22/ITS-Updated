"""
backend/app/api/ask.py
POST /api/ask    — RAG-powered unified ask endpoint
GET  /api/tutor/history/{student_id} — recent chat history (spec endpoint)

Returns { response, cited_chunks, concept, mastery_before }
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.auth.auth_service import get_current_student
from app.application.tutor_service import get_answer
from app.infrastructure import chat_repository

router = APIRouter(prefix="/api", tags=["ask"])


class AskRequest(BaseModel):
    question: str


class CitedChunk(BaseModel):
    id:          int
    excerpt:     str
    similarity:  float
    page_number: int


class AskResponse(BaseModel):
    response:       str
    concept:        str
    mastery_before: float
    cited_chunks:   list[CitedChunk]


class MessageOut(BaseModel):
    id:         int
    role:       str
    content:    str
    created_at: str


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, student_id: str = Depends(get_current_student)):
    """RAG-powered ask endpoint — retrieves context and calls Groq LLM."""
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")
    try:
        result = await get_answer(question=req.question.strip(), student_id=student_id)
        return AskResponse(
            response=result["answer"],
            concept=result["concept_detected"],
            mastery_before=result["mastery_before"],
            cited_chunks=result.get("cited_chunks", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tutor error: {e}")


@router.get("/tutor/history/{student_id}", response_model=list[MessageOut])
async def tutor_history(
    student_id: str,
    limit: int = Query(default=5, ge=1, le=50),
    _current: str = Depends(get_current_student),
):
    """
    Return the last {limit} chat messages for a student.
    Spec endpoint: GET /api/tutor/history/{student_id}?limit=5
    """
    rows = await chat_repository.get_recent_messages(student_id, limit=limit)
    return [
        MessageOut(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            created_at=str(r.get("created_at", "")),
        )
        for r in rows
    ]
