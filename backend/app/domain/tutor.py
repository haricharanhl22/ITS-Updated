"""
Tutor domain models — Pydantic schemas for chat, mastery, assessment, and event logging.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# ── Chat ──────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    student_id: int
    question: str


class AskResponse(BaseModel):
    answer: str
    concept_detected: str  # always present — sidebar depends on this


class ChatMessageOut(BaseModel):
    id: int
    role: str          # "user" | "assistant"
    content: str
    concept: Optional[str] = None
    created_at: str


# ── Mastery ───────────────────────────────────────────────────────────────────

class MasteryRecord(BaseModel):
    concept: str
    score: float       # 0.0 – 1.0


# ── Assessment ────────────────────────────────────────────────────────────────

class AssessmentQuestion(BaseModel):
    id: int
    text: str
    options: list[str]  # exactly 4 options: A, B, C, D
    correct_index: int  # 0-based index of correct option
    difficulty: str = "easy"  # 'easy' | 'hard'


class AssessmentOut(BaseModel):
    concept: str
    questions: list[AssessmentQuestion]


class SubmitRequest(BaseModel):
    student_id: int
    concept: str
    answers: dict[str, int]  # { "0": 2, "1": 0, ... }  question_id → chosen_index


class SubmitResponse(BaseModel):
    score: float         # fraction correct, e.g. 0.8
    correct_count: int
    total: int
    new_mastery: float   # updated BKU mastery (0.0 – 1.0)
    mastery_delta: float # change in mastery (can be negative)
    difficulty_served: str = "easy"  # 'easy' | 'hard' — which tier was served


# ── AI-Generated Quiz (Groq-backed, per-attempt) ──────────────────────────────
# Same shape as AssessmentQuestion/AssessmentOut/SubmitRequest/SubmitResponse
# above, extended with the fields a generated-per-attempt quiz needs
# (assessment_id to grade against, explanation from Groq). The static
# assessment_* models above are untouched and still used by the old quiz flow.

class GeneratedQuestion(BaseModel):
    id: int
    text: str
    options: list[str]     # exactly 4 options
    correct_index: int     # 0-based index of correct option
    difficulty: str         # 'easy' | 'hard' — same tier for every question in the quiz
    explanation: str        # short explanation of the correct answer, from Groq


class GeneratedAssessmentOut(BaseModel):
    assessment_id: int
    concept: str
    difficulty: str
    questions: list[GeneratedQuestion]


class GeneratedSubmitRequest(BaseModel):
    student_id: int
    assessment_id: int
    answers: dict[str, int]  # { "0": 2, "1": 0, ... } question_id -> chosen_index


class GeneratedSubmitResponse(BaseModel):
    score: float
    correct_count: int
    total: int
    new_mastery: float
    mastery_delta: float
    difficulty_served: str


# ── Learning Events ───────────────────────────────────────────────────────────

class LearningEvent(BaseModel):
    student_id: int
    concept: str
    score: float
    assessment_id: Optional[str] = None
    event_type: str = "quiz"
