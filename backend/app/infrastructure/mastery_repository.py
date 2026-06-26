"""
Mastery repository — aligned with real Supabase schema.

Table: student_mastery
Columns: id, student_id (bigint), concept_name, mastery_score, attempts, last_updated

UNIQUE constraint: (student_id, concept_name) — required for upsert.
"""
from datetime import datetime, timezone

from app.config.supabase_client import supabase


def get_mastery(student_id: int) -> list[dict]:
    """Return all concept mastery records for a student, sorted by concept name."""
    result = (
        supabase.table("student_mastery")
        .select("concept_name, mastery_score, attempts, last_updated")
        .eq("student_id", student_id)
        .order("concept_name")
        .execute()
    )
    return result.data or []


def get_weak_concepts(student_id: int, threshold: float = 0.5) -> list[dict]:
    """Return concepts where mastery_score < threshold (default 0.5)."""
    result = (
        supabase.table("student_mastery")
        .select("concept_name, mastery_score, attempts, last_updated")
        .eq("student_id", student_id)
        .lt("mastery_score", threshold)
        .order("mastery_score")
        .execute()
    )
    return result.data or []


def get_strong_concepts(student_id: int, threshold: float = 0.7) -> list[dict]:
    """Return concepts where mastery_score > threshold (default 0.7)."""
    result = (
        supabase.table("student_mastery")
        .select("concept_name, mastery_score, attempts, last_updated")
        .eq("student_id", student_id)
        .gt("mastery_score", threshold)
        .order("mastery_score", desc=True)
        .execute()
    )
    return result.data or []


def upsert_mastery(student_id: int, concept_name: str, score: float) -> dict:
    """
    Insert or update mastery for (student_id, concept_name).
    Increments attempts and updates mastery_score and last_updated.
    Uses Supabase upsert with on_conflict to handle the UNIQUE constraint.
    """
    now = datetime.now(timezone.utc).isoformat()

    # First get current attempts count for increment
    existing = (
        supabase.table("student_mastery")
        .select("attempts")
        .eq("student_id", student_id)
        .eq("concept_name", concept_name)
        .limit(1)
        .execute()
    )
    current_attempts = (existing.data[0]["attempts"] or 0) if existing.data else 0

    result = (
        supabase.table("student_mastery")
        .upsert(
            {
                "student_id": student_id,
                "concept_name": concept_name,
                "mastery_score": round(max(0.0, min(1.0, score)), 4),
                "attempts": current_attempts + 1,
                "last_updated": now,
            },
            on_conflict="student_id,concept_name",
        )
        .execute()
    )
    return result.data[0] if result.data else {}


def get_concept_mastery(student_id: int, concept_name: str) -> float:
    """Return a single concept's mastery score (0.0 if not yet attempted)."""
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
