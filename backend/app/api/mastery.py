"""
Mastery API router.

Endpoints:
  GET /mastery/        — all concept scores for the authenticated student
  GET /mastery/weak    — concepts with mastery < 0.5
  GET /mastery/strong  — concepts with mastery > 0.7

Used by the sidebar, dashboard, and MasteryDashboard component.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_service import get_current_student
from app.domain.tutor import MasteryRecord
from app.infrastructure import mastery_repository

router = APIRouter(prefix="/mastery", tags=["mastery"])


@router.get("", response_model=list[MasteryRecord])
def get_mastery(student_id: str = Depends(get_current_student)):
    """Return all concept mastery scores for a student."""
    rows = mastery_repository.get_mastery(student_id)
    return [
        MasteryRecord(
            concept=r["concept_name"],
            score=float(r["mastery_score"] or 0.0),
        )
        for r in rows
    ]


@router.get("/{student_id}", response_model=list[MasteryRecord])
def get_student_mastery(student_id: str):
    """Return all concept mastery scores for a specific student ID."""
    rows = mastery_repository.get_mastery(student_id)
    return [
        MasteryRecord(
            concept=r["concept_name"],
            score=float(r["mastery_score"] or 0.0),
        )
        for r in rows
    ]


@router.get("/weak", response_model=list[MasteryRecord])
def get_weak_concepts(student_id: str = Depends(get_current_student)):
    """Return concepts with mastery_score < 0.5 (needs practice)."""
    rows = mastery_repository.get_weak_concepts(student_id, threshold=0.5)
    return [
        MasteryRecord(
            concept=r["concept_name"],
            score=float(r["mastery_score"] or 0.0),
        )
        for r in rows
    ]


@router.get("/strong", response_model=list[MasteryRecord])
def get_strong_concepts(student_id: str = Depends(get_current_student)):
    """Return concepts with mastery_score > 0.7 (well understood)."""
    rows = mastery_repository.get_strong_concepts(student_id, threshold=0.7)
    return [
        MasteryRecord(
            concept=r["concept_name"],
            score=float(r["mastery_score"] or 0.0),
        )
        for r in rows
    ]
