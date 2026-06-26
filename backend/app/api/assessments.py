"""
backend/app/api/assessments.py
FastAPI router — GET /assessments/{concept}  and  POST /assessments/submit

CHANGED: Full async/await. POST /assessments/submit now explicitly:
  1. Scores submitted answers vs correct answers
  2. Fetches old mastery_score from student_mastery via supabase-py
  3. Computes new_mastery = (old_mastery * 0.7) + (quiz_score * 0.3)
  4. Upserts student_mastery (concept_name, mastery_score, attempts, last_updated)
  5. Inserts a row into learning_events
     (student_id, concept_name, assessment_id, score, created_at)

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

router = APIRouter(prefix="/assessments", tags=["assessments"])

# Correct-answer letter → 0-based index
_LETTER_TO_IDX = {"A": 0, "B": 1, "C": 2, "D": 3}


# ── Request / Response models ─────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id:            int
    text:          str
    options:       list[str]
    correct_index: int


class AssessmentOut(BaseModel):
    concept:   str
    questions: list[QuestionOut]


class SubmitRequest(BaseModel):
    concept:    str
    answers:    dict[str, int]   # {"0": 2, "1": 0, ...}  — 0-based option index


class SubmitResponse(BaseModel):
    score:         float
    correct_count: int
    total:         int
    new_mastery:   float
    mastery_delta: float


# ── Supabase helpers (sync, wrapped in to_thread) ─────────────────────────────

def _fetch_assessment(concept_name: str) -> Optional[dict]:
    result = (
        supabase.table("assessments")
        .select("id, concept_name, title")
        .eq("concept_name", concept_name)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _fetch_questions(assessment_id: int) -> list[dict]:
    result = (
        supabase.table("assessment_questions")
        .select("id, question_text, option_a, option_b, option_c, option_d, correct_answer")
        .eq("assessment_id", assessment_id)
        .execute()
    )
    return result.data or []


def _get_old_mastery(student_id: str, concept_name: str) -> float:
    result = (
        supabase.table("student_mastery")
        .select("mastery_score")
        .eq("student_id", student_id)
        .eq("concept_name", concept_name)
        .limit(1)
        .execute()
    )
    if result.data:
        return float(result.data[0]["mastery_score"] or 0.0)
    return 0.0


def _upsert_mastery(student_id: str, concept_name: str, new_mastery: float):
    # First get current attempts
    existing = (
        supabase.table("student_mastery")
        .select("attempts")
        .eq("student_id", student_id)
        .eq("concept_name", concept_name)
        .limit(1)
        .execute()
    )
    attempts = (existing.data[0]["attempts"] or 0) + 1 if existing.data else 1

    supabase.table("student_mastery").upsert(
        {
            "student_id":   student_id,
            "concept_name": concept_name,
            "mastery_score": round(new_mastery, 4),
            "attempts":     attempts,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="student_id,concept_name",
    ).execute()


def _insert_learning_event(
    student_id: str,
    concept_name: str,
    assessment_id: int,
    score: float,
):
    supabase.table("learning_events").insert({
        "student_id":    student_id,
        "concept_name":  concept_name,
        "assessment_id": assessment_id,
        "score":         round(score, 4),
        "created_at":    datetime.now(timezone.utc).isoformat(),
    }).execute()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{concept}", response_model=AssessmentOut)
async def fetch_assessment(
    concept: str,
    student_id: str = Depends(get_current_student),
):
    """
    Return questions for a Python concept from the assessments + assessment_questions tables.
    Returns 404 if the concept has no assessment seeded.
    """
    assessment = await asyncio.to_thread(_fetch_assessment, concept)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment found for concept '{concept}'. Seed the assessments table first.",
        )

    raw_qs = await asyncio.to_thread(_fetch_questions, assessment["id"])
    if not raw_qs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment for '{concept}' has no questions. Run the seed SQL.",
        )

    questions = []
    for i, q in enumerate(raw_qs):
        correct_letter = (q.get("correct_answer") or "A").upper()
        questions.append(QuestionOut(
            id=i,
            text=q["question_text"],
            options=[
                q.get("option_a") or "",
                q.get("option_b") or "",
                q.get("option_c") or "",
                q.get("option_d") or "",
            ],
            correct_index=_LETTER_TO_IDX.get(correct_letter, 0),
        ))

    return AssessmentOut(concept=concept, questions=questions)


@router.post("/submit", response_model=SubmitResponse)
async def submit(
    req: SubmitRequest,
    student_id: str = Depends(get_current_student),
):
    """
    Score the quiz, update student_mastery via EMA, and write a learning_events row.

    EMA formula:  new_mastery = (old_mastery * 0.7) + (quiz_score * 0.3)
    Bounded to [0.0, 1.0].

    Steps:
      1. Fetch assessment + questions from Supabase
      2. Score submitted answers vs correct_answer letters
      3. Fetch old mastery_score from student_mastery
      4. Compute new_mastery via EMA
      5. Upsert student_mastery (increments attempts)
      6. Insert row into learning_events (assessment_id = bigint FK)
    """
    sid = student_id

    # 1. Fetch assessment
    assessment = await asyncio.to_thread(_fetch_assessment, req.concept)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No assessment for concept '{req.concept}'.",
        )

    raw_qs = await asyncio.to_thread(_fetch_questions, assessment["id"])
    if not raw_qs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No questions found for concept '{req.concept}'.",
        )

    # 2. Score
    total         = len(raw_qs)
    correct_count = 0
    for i, q in enumerate(raw_qs):
        correct_letter = (q.get("correct_answer") or "A").upper()
        correct_idx    = _LETTER_TO_IDX.get(correct_letter, 0)
        chosen         = req.answers.get(str(i))
        if chosen is not None and chosen == correct_idx:
            correct_count += 1

    quiz_score = correct_count / total if total > 0 else 0.0

    # 3. Fetch old mastery
    old_mastery = await asyncio.to_thread(_get_old_mastery, sid, req.concept)

    # 4. EMA formula
    new_mastery = round(
        max(0.0, min(1.0, old_mastery * 0.7 + quiz_score * 0.3)),
        4,
    )
    mastery_delta = round(new_mastery - old_mastery, 4)

    # 5. Upsert student_mastery
    await asyncio.to_thread(_upsert_mastery, sid, req.concept, new_mastery)

    # 6. Insert learning_events row (this step was missing — now added)
    await asyncio.to_thread(
        _insert_learning_event,
        sid,
        req.concept,
        assessment["id"],
        quiz_score,
    )

    return SubmitResponse(
        score=round(quiz_score, 4),
        correct_count=correct_count,
        total=total,
        new_mastery=new_mastery,
        mastery_delta=mastery_delta,
    )
