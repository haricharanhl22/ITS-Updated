"""
backend/app/api/assessments.py
FastAPI router — GET /assessments/{concept}  and  POST /assessments/submit

ADAPTIVE DIFFICULTY + BKU SCORING:
  1. GET /assessments/{concept}
     - Fetches student mastery for the concept via JWT-authenticated student_id
     - mastery < 0.65 → serves 'easy' questions; >= 0.65 → 'hard' questions
     - Returns questions with their difficulty tag

  2. POST /assessments/submit
     - Scores each answer individually using Bayesian Knowledge Update (BKU)
     - Correct: Δ = gain_rate × (1 - mastery) × difficulty_weight
     - Wrong:   Δ = loss_rate × mastery       × difficulty_weight
     - Upserts student_mastery and inserts learning_events row

All DB calls are wrapped in asyncio.to_thread() to stay non-blocking.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.auth.auth_service import get_current_student
from app.config.supabase_client import supabase
from app.application.assessment_service import (
    get_assessment as svc_get_assessment,
    submit_assessment as svc_submit_assessment,
    MASTERY_THRESHOLD,
)
from app.domain.tutor import SubmitRequest

router = APIRouter(prefix="/assessments", tags=["assessments"])


# ── Request / Response models ─────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id:            int
    text:          str
    options:       list[str]
    correct_index: int
    difficulty:    str = "easy"   # 'easy' | 'hard'


class AssessmentOut(BaseModel):
    concept:   str
    questions: list[QuestionOut]


class SubmitRequestBody(BaseModel):
    concept:    str
    answers:    dict[str, int]   # {"0": 2, "1": 0, ...}  — 0-based option index


class SubmitResponse(BaseModel):
    score:             float
    correct_count:     int
    total:             int
    new_mastery:       float
    mastery_delta:     float
    difficulty_served: str = "easy"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{concept}", response_model=AssessmentOut)
async def fetch_assessment(
    concept: str,
    student_id: str = Depends(get_current_student),
):
    """
    Return questions for a Python concept, adaptively filtered by difficulty.

    The student's mastery score determines which tier is served:
      - mastery < 0.65 → easy questions
      - mastery >= 0.65 → hard questions

    Returns 404 if the concept has no assessment seeded.
    """
    try:
        result = await asyncio.to_thread(svc_get_assessment, concept, student_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Convert domain objects to API response models
    questions = [
        QuestionOut(
            id=q.id,
            text=q.text,
            options=q.options,
            correct_index=q.correct_index,
            difficulty=q.difficulty,
        )
        for q in result.questions
    ]

    return AssessmentOut(concept=result.concept, questions=questions)


@router.post("/submit", response_model=SubmitResponse)
async def submit(
    req: SubmitRequestBody,
    student_id: str = Depends(get_current_student),
):
    """
    Score the quiz using per-question Bayesian Knowledge Update (BKU).

    BKU formula (applied per question):
      Correct: Δ = gain_rate × (1 - mastery) × difficulty_weight
      Wrong:   Δ = loss_rate × mastery       × difficulty_weight

    Steps:
      1. Fetch assessment + questions from Supabase
      2. Score each submitted answer individually with BKU
      3. Upsert student_mastery with the final running mastery
      4. Insert row into learning_events
    """
    # Build the domain SubmitRequest with student_id from JWT
    domain_req = SubmitRequest(
        student_id=student_id,
        concept=req.concept,
        answers=req.answers,
    )

    try:
        result = await asyncio.to_thread(svc_submit_assessment, domain_req)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return SubmitResponse(
        score=result.score,
        correct_count=result.correct_count,
        total=result.total,
        new_mastery=result.new_mastery,
        mastery_delta=result.mastery_delta,
        difficulty_served=result.difficulty_served,
    )
