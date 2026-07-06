"""
backend/app/api/quiz.py
FastAPI router — AI-generated adaptive quiz (Groq + RAG), additive to the
existing static quiz endpoints in app/api/assessments.py (left untouched).

Endpoints:
  GET  /quiz/generate/{concept}  — generate a fresh 5-question quiz for a concept
  POST /quiz/submit              — grade a generated-quiz attempt, update mastery

All business logic lives in app/application/quiz_generation_service.py; this
router only translates HTTP <-> service calls, matching the existing
api/assessments.py style.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.application.quiz_generation_service import QuizGenerationError, QuizRateLimitError
from app.application import quiz_generation_service as svc
from app.auth.auth_service import get_current_student
from app.domain.tutor import GeneratedAssessmentOut, GeneratedSubmitResponse

router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizSubmitBody(BaseModel):
    assessment_id: int
    answers: dict[str, int]   # {"0": 2, "1": 0, ...} — 0-based option index
    hints_used: dict[str, bool] = {}   # {"0": true, "1": false, ...} — same keying as answers


@router.get("/generate/{concept}", response_model=GeneratedAssessmentOut)
async def generate_quiz(
    concept: str,
    student_id: str = Depends(get_current_student),
):
    """
    Generate a brand-new 5-question quiz for `concept`, using the student's
    current mastery to pick easy/hard, the existing RAG pipeline to retrieve
    textbook context, and Groq to write the questions.
    """
    try:
        return await svc.generate_quiz(student_id=student_id, concept=concept)
    except ValueError as e:
        # Unknown concept
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuizRateLimitError as e:
        # Groq's daily/per-minute quota is exhausted — retrying won't help until
        # it cools down, so surface a 429 with a Retry-After hint instead of a
        # generic 500. Caught before QuizGenerationError since it's a subclass.
        headers = {"Retry-After": str(round(e.retry_after_seconds))} if e.retry_after_seconds else None
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e), headers=headers)
    except QuizGenerationError as e:
        # No RAG context, or Groq failed validation after all retries
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Quiz generation error: {e}")


@router.post("/submit", response_model=GeneratedSubmitResponse)
async def submit_quiz(
    req: QuizSubmitBody,
    student_id: str = Depends(get_current_student),
):
    """
    Grade a generated-quiz attempt server-side against the stored correct
    answers, update mastery via the existing BKU formula, and log a
    learning_events row.
    """
    try:
        return await asyncio.to_thread(
            svc.submit_quiz,
            student_id=student_id,
            assessment_id=req.assessment_id,
            answers=req.answers,
            hints_used=req.hints_used,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Quiz submission error: {e}")
