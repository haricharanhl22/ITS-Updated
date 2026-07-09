"""
Mastery API router.

Endpoints:
  GET /mastery/         — all concept scores for the authenticated student
  GET /mastery/overall  — curriculum-wide overall mastery (weighted average
                          across ALL concepts, unattempted ones count as 0)
  GET /mastery/weak     — concepts with mastery < 0.5
  GET /mastery/strong   — concepts with mastery > 0.7

Used by the sidebar, dashboard, and MasteryDashboard component.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_service import get_current_student
from app.domain.mastery_scoring import CONCEPT_WEIGHTS, compute_overall_mastery
from app.domain.tutor import MasteryRecord, OverallMasteryOut
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


@router.get("/overall", response_model=OverallMasteryOut)
def get_overall_mastery(student_id: str = Depends(get_current_student)):
    """
    Return the student's curriculum-wide overall mastery.

    Unlike GET /mastery (which only returns rows for concepts the student
    has attempted), this treats every concept in CONCEPT_WEIGHTS as part of
    the calculation -- unattempted concepts contribute a score of 0, so a
    single perfect quiz does not inflate the overall number.

    Registered before /{student_id} so "overall" is never swallowed by the
    path-param route below.
    """
    rows = mastery_repository.get_mastery(student_id)
    concept_scores = {r["concept_name"]: float(r["mastery_score"] or 0.0) for r in rows}
    overall = compute_overall_mastery(concept_scores, weighted=True)
    return OverallMasteryOut(
        overall_mastery=overall,
        weighted=True,
        concepts_attempted=len(concept_scores),
        concepts_total=len(CONCEPT_WEIGHTS),
    )


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
