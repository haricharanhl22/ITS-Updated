"""
backend/app/infrastructure/generated_quiz_repository.py
Repository for the AI-generated quiz tables (additive — does not touch the
existing `assessments` / `assessment_questions` tables used by the static quiz).

Tables:
  generated_assessments — one row per quiz ATTEMPT
    id, student_id (bigint), concept_name, difficulty ('easy'|'hard'), created_at
  generated_questions — the 5 MCQs belonging to one generated_assessments row
    id, assessment_id (FK), question_text, option_a..d, correct_answer ('A'..'D'),
    explanation, created_at
"""
from datetime import datetime, timezone
from typing import Optional

from app.config.supabase_client import supabase

ASSESSMENTS_TABLE = "generated_assessments"
QUESTIONS_TABLE = "generated_questions"


def create_assessment(student_id: int, concept_name: str, difficulty: str) -> int:
    """Insert a new generated_assessments row and return its id."""
    result = (
        supabase.table(ASSESSMENTS_TABLE)
        .insert({
            "student_id": student_id,
            "concept_name": concept_name,
            "difficulty": difficulty,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        .execute()
    )
    return result.data[0]["id"]


def insert_questions(assessment_id: int, questions: list[dict]) -> list[dict]:
    """
    Bulk-insert the generated questions for one assessment.
    Each question dict must have: question_text, option_a..d, correct_answer, explanation.
    Returns the inserted rows (including their DB ids, in insertion order).
    """
    rows = [
        {
            "assessment_id": assessment_id,
            "question_text": q["question_text"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "hint": q["hint"],
        }
        for q in questions
    ]
    result = supabase.table(QUESTIONS_TABLE).insert(rows).execute()
    return result.data or []


def get_assessment(assessment_id: int) -> Optional[dict]:
    """Fetch a generated_assessments row by id, or None if it doesn't exist."""
    result = (
        supabase.table(ASSESSMENTS_TABLE)
        .select("id, student_id, concept_name, difficulty, created_at")
        .eq("id", assessment_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_questions(assessment_id: int) -> list[dict]:
    """Return all questions for a generated assessment, in insertion (id) order."""
    result = (
        supabase.table(QUESTIONS_TABLE)
        .select("id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, hint")
        .eq("assessment_id", assessment_id)
        .order("id")
        .execute()
    )
    return result.data or []


def mark_hints_used(row_ids: list[int]) -> None:
    """
    Flip hint_used = true for the given generated_questions row ids. Called
    once per submit_quiz(), for exactly the questions the student actually
    revealed a hint on in this attempt. No-op if the list is empty.
    """
    if not row_ids:
        return
    supabase.table(QUESTIONS_TABLE).update({"hint_used": True}).in_("id", row_ids).execute()


def get_previous_question_texts(
    student_id: int,
    concept_name: str,
    difficulty: str,
    limit: int = 20,
) -> list[str]:
    """
    Return question_text values from this student's past generated quizzes for
    (concept_name, difficulty) — e.g. all EASY-tier questions already asked for
    this concept, so a later HARD-tier quiz can try not to repeat them.

    Two queries instead of a PostgREST embedded join, to keep this readable and
    avoid relying on postgrest-py's join-filter syntax for a simple lookup.
    """
    assessments_result = (
        supabase.table(ASSESSMENTS_TABLE)
        .select("id")
        .eq("student_id", student_id)
        .eq("concept_name", concept_name)
        .eq("difficulty", difficulty)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    assessment_ids = [row["id"] for row in (assessments_result.data or [])]
    if not assessment_ids:
        return []

    questions_result = (
        supabase.table(QUESTIONS_TABLE)
        .select("question_text")
        .in_("assessment_id", assessment_ids)
        .execute()
    )
    return [row["question_text"] for row in (questions_result.data or [])]
