from __future__ import annotations

"""
Assessment service — adaptive difficulty + Bayesian Knowledge Update (BKU) scoring.

DB Schema:
  assessments:          id (bigint), concept_name, title, created_at
  assessment_questions: id, assessment_id (FK→assessments.id),
                        question_text, option_a … option_d,
                        correct_answer ('A'|'B'|'C'|'D'),
                        difficulty ('easy'|'hard'),
                        concept_name (denormalized)

Adaptive flow:
  1. Look up student mastery for the requested concept
  2. mastery < MASTERY_THRESHOLD → serve 'easy' questions; else → 'hard'
  3. On submit, score each answer individually with the BKU formula

BKU formula (per question):
  correct:  Δ = gain_rate × (1 - mastery) × difficulty_weight
  wrong:    Δ = loss_rate × mastery       × difficulty_weight
  Clamped to [0.0, 1.0]
"""
from app.config.supabase_client import supabase
from app.domain.tutor import AssessmentOut, AssessmentQuestion, SubmitRequest, SubmitResponse
from app.infrastructure import mastery_repository, learning_events_repository

# ── Scoring constants ─────────────────────────────────────────────────────────

# Map letter answers to 0-based indices for scoring
_LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}

# Mastery threshold: below → easy; at or above → hard
MASTERY_THRESHOLD = 0.65

# BKU tuning parameters
GAIN_RATE = 0.15   # conservative gain per correct answer
LOSS_RATE = 0.10   # gentler penalty per wrong answer

# Difficulty weights: (difficulty, is_correct) → weight
DIFFICULTY_WEIGHTS = {
    ("easy", True):   0.8,   # easy correct  → smaller reward
    ("easy", False):  1.2,   # easy wrong    → heavier penalty
    ("hard", True):   1.5,   # hard correct  → big reward
    ("hard", False):  0.6,   # hard wrong    → lighter penalty
}


# ── Supabase helpers ──────────────────────────────────────────────────────────

def _get_assessment_row(concept_name: str) -> dict:
    """Fetch the assessments row for a concept. Raises ValueError if not found."""
    result = (
        supabase.table("assessments")
        .select("id, concept_name, title")
        .eq("concept_name", concept_name)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError(
            f"No assessment found for concept '{concept_name}'. "
            f"Check the assessments table has this concept_name."
        )
    return result.data[0]


def _get_questions(assessment_id: int, difficulty: str | None = None) -> list[dict]:
    """
    Fetch questions for an assessment from Supabase.
    If difficulty is provided, filter to that tier only.
    """
    query = (
        supabase.table("assessment_questions")
        .select("id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty, concept_name")
        .eq("assessment_id", assessment_id)
    )
    if difficulty:
        query = query.eq("difficulty", difficulty)

    result = query.execute()
    return result.data or []


def _determine_difficulty(mastery_score: float) -> str:
    """Return 'easy' or 'hard' based on mastery threshold."""
    return "hard" if mastery_score >= MASTERY_THRESHOLD else "easy"


def _compute_bku_update(
    current_mastery: float,
    is_correct: bool,
    difficulty: str,
) -> float:
    """
    Compute the new mastery score after a single question using BKU.

    Correct:  new = mastery + gain_rate × (1 - mastery) × weight
    Wrong:    new = mastery - loss_rate × mastery       × weight
    Clamped to [0.0, 1.0].
    """
    weight = DIFFICULTY_WEIGHTS.get((difficulty, is_correct), 1.0)

    if is_correct:
        delta = GAIN_RATE * (1.0 - current_mastery) * weight
        new_mastery = current_mastery + delta
    else:
        delta = LOSS_RATE * current_mastery * weight
        new_mastery = current_mastery - delta

    return round(max(0.0, min(1.0, new_mastery)), 4)


# ── Public API ────────────────────────────────────────────────────────────────

def get_assessment(concept_name: str, student_id: int | str | None = None) -> AssessmentOut:
    """
    Return questions for a concept, filtered by adaptive difficulty.

    If student_id is provided, look up mastery and serve the appropriate
    difficulty tier.  If not provided (or mastery lookup fails), serve
    all questions (backwards-compatible behaviour).
    """
    assessment = _get_assessment_row(concept_name)

    # Determine difficulty tier from student mastery
    difficulty_filter: str | None = None
    if student_id is not None:
        try:
            mastery = mastery_repository.get_concept_mastery(student_id, concept_name)
            difficulty_filter = _determine_difficulty(mastery)
        except Exception:
            difficulty_filter = None  # fall back to all questions

    raw_questions = _get_questions(assessment["id"], difficulty=difficulty_filter)

    # Fallback: if no questions found for the filtered difficulty, serve all
    if not raw_questions:
        raw_questions = _get_questions(assessment["id"])

    if not raw_questions:
        raise ValueError(
            f"Assessment for '{concept_name}' exists but has no questions. "
            f"Run the seed SQL to populate assessment_questions."
        )

    questions = []
    for i, q in enumerate(raw_questions):
        correct_letter = (q.get("correct_answer") or "A").upper()
        correct_index = _LETTER_TO_INDEX.get(correct_letter, 0)

        questions.append(AssessmentQuestion(
            id=i,                          # 0-based index for frontend answer mapping
            text=q["question_text"],
            options=[
                q.get("option_a") or "",
                q.get("option_b") or "",
                q.get("option_c") or "",
                q.get("option_d") or "",
            ],
            correct_index=correct_index,
            difficulty=q.get("difficulty", "easy"),
        ))

    return AssessmentOut(concept=concept_name, questions=questions)


def submit_assessment(req: SubmitRequest) -> SubmitResponse:
    """
    Score the quiz with per-question BKU updates, write mastery + learning event.

    BKU formula (per question):
      correct:  Δ = gain_rate × (1 - mastery) × difficulty_weight
      wrong:    Δ = loss_rate × mastery       × difficulty_weight

    Each question's difficulty is read from the DB row for accurate weighting.
    """
    # Fetch assessment + questions (validates concept exists)
    assessment_row = _get_assessment_row(req.concept)
    assessment_db_id: int = assessment_row["id"]

    # ── Fetch current mastery ─────────────────────────────────────────────
    old_mastery = mastery_repository.get_concept_mastery(req.student_id, req.concept)
    running_mastery = old_mastery

    # Determine difficulty tier that was served to the student
    difficulty_filter = _determine_difficulty(old_mastery)
    raw_questions = _get_questions(assessment_db_id, difficulty=difficulty_filter)
    if not raw_questions:
        raw_questions = _get_questions(assessment_db_id)

    if not raw_questions:
        raise ValueError(f"No questions found for concept '{req.concept}'")

    total = len(raw_questions)
    correct_count = 0

    # Track which difficulty tier was actually served (majority vote)
    difficulty_counts = {"easy": 0, "hard": 0}

    # ── Per-question BKU scoring ──────────────────────────────────────────
    for i, q in enumerate(raw_questions):
        correct_letter = (q.get("correct_answer") or "A").upper()
        correct_index = _LETTER_TO_INDEX.get(correct_letter, 0)
        q_difficulty = q.get("difficulty", "easy")
        difficulty_counts[q_difficulty] = difficulty_counts.get(q_difficulty, 0) + 1

        # Student answers keyed by 0-based question index (as string)
        chosen = req.answers.get(str(i))
        is_correct = (chosen is not None and chosen == correct_index)

        if is_correct:
            correct_count += 1

        # Apply BKU update for this question
        running_mastery = _compute_bku_update(running_mastery, is_correct, q_difficulty)

    # Determine which difficulty was predominantly served
    difficulty_served = "hard" if difficulty_counts.get("hard", 0) >= difficulty_counts.get("easy", 0) else "easy"

    if difficulty_served == "hard" and correct_count == total and total > 0:
        new_mastery = 1.0
    elif correct_count == total and total > 0:
        new_mastery = max(old_mastery, running_mastery)
    else:
        new_mastery = running_mastery

    new_mastery = round(max(0.0, min(1.0, new_mastery)), 4)
    quiz_score = correct_count / total if total > 0 else 0.0

    # ── Persist mastery ───────────────────────────────────────────────────
    mastery_repository.upsert_mastery(req.student_id, req.concept, new_mastery)

    # ── Write learning event (thesis evidence, assessment_id as bigint FK) ─
    learning_events_repository.insert_event(
        student_id=req.student_id,
        concept_name=req.concept,
        score=quiz_score,
        assessment_id=assessment_db_id,   # real bigint FK
    )

    return SubmitResponse(
        score=round(quiz_score, 4),
        correct_count=correct_count,
        total=total,
        new_mastery=new_mastery,
        mastery_delta=round(new_mastery - old_mastery, 4),
        difficulty_served=difficulty_served,
    )
