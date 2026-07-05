"""
Learning events repository — aligned with real Supabase schema.

Table: learning_events
Columns: id, student_id (bigint), concept_name, assessment_id (bigint), score, created_at

NOTE: No 'event_type' column exists in the schema — removed from insert.
assessment_id is a bigint FK to assessments.id, not a generated string.
"""
from datetime import datetime, timezone
from typing import Optional

from app.config.supabase_client import supabase


def insert_event(
    student_id: int,
    concept_name: str,
    score: float,
    assessment_id: Optional[int] = None,
    generated_assessment_id: Optional[int] = None,
) -> dict:
    """
    Insert an immutable learning event row.
    Called every time a quiz is submitted — never updated or deleted.
    assessment_id must be the bigint PK from the (static) assessments table, or None.
    generated_assessment_id must be the bigint PK from generated_assessments (the
    AI-generated quiz flow), or None. At most one of the two is normally set.
    """
    result = (
        supabase.table("learning_events")
        .insert({
            "student_id": student_id,
            "concept_name": concept_name,
            "score": round(score, 4),
            "assessment_id": assessment_id,
            "generated_assessment_id": generated_assessment_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        .execute()
    )
    return result.data[0] if result.data else {}


def get_events_for_student(student_id: int) -> list[dict]:
    """Return all learning events for a student, newest first."""
    result = (
        supabase.table("learning_events")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
