"""
Assessment service — reads questions from Supabase assessments + assessment_questions tables.

DB Schema:
  assessments:         id (bigint), concept_name, title, created_at
  assessment_questions: id, assessment_id (FK→assessments.id),
                        question_text, option_a, option_b, option_c, option_d,
                        correct_answer (text: 'A'|'B'|'C'|'D')

Scoring:
  EMA formula: new_mastery = old_mastery * 0.7 + quiz_score * 0.3
  correct_answer 'A'→0, 'B'→1, 'C'→2, 'D'→3  (for comparison with student's 0-based index)
"""
from app.config.supabase_client import supabase
from app.domain.tutor import AssessmentOut, AssessmentQuestion, SubmitRequest, SubmitResponse
from app.infrastructure import mastery_repository, learning_events_repository

# Map letter answers to 0-based indices for scoring
_LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


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


def _get_questions(assessment_id: int) -> list[dict]:
    """Fetch all questions for an assessment from Supabase."""
    result = (
        supabase.table("assessment_questions")
        .select("id, question_text, option_a, option_b, option_c, option_d, correct_answer")
        .eq("assessment_id", assessment_id)
        .execute()
    )
    return result.data or []


def get_assessment(concept_name: str) -> AssessmentOut:
    """
    Return questions for a concept from Supabase.
    Converts option_a/b/c/d columns and correct_answer letter to AssessmentQuestion objects.
    """
    assessment = _get_assessment_row(concept_name)
    raw_questions = _get_questions(assessment["id"])

    if not raw_questions:
        raise ValueError(
            f"Assessment for '{concept_name}' exists but has no questions. "
            f"Run the seed SQL to populate assessment_questions."
        )

    questions = []
    for i, q in enumerate(raw_questions):
        correct_letter = (q.get("correct_answer") or "A").upper()
        correct_index  = _LETTER_TO_INDEX.get(correct_letter, 0)

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
        ))

    return AssessmentOut(concept=concept_name, questions=questions)


def submit_assessment(req: SubmitRequest) -> SubmitResponse:
    """
    Score the quiz, update mastery via EMA, write learning_events.

    EMA formula: new_mastery = old_mastery * 0.7 + quiz_score * 0.3
    Bounds: clamped to [0.0, 1.0].

    assessment_id is the bigint PK from the assessments table.
    """
    # Fetch assessment + questions (validates concept exists)
    assessment_row = _get_assessment_row(req.concept)
    assessment_db_id: int = assessment_row["id"]
    raw_questions = _get_questions(assessment_db_id)

    if not raw_questions:
        raise ValueError(f"No questions found for concept '{req.concept}'")

    total = len(raw_questions)
    correct_count = 0

    for i, q in enumerate(raw_questions):
        correct_letter = (q.get("correct_answer") or "A").upper()
        correct_index  = _LETTER_TO_INDEX.get(correct_letter, 0)
        # Student answers keyed by 0-based question index (as string)
        chosen = req.answers.get(str(i))
        if chosen is not None and chosen == correct_index:
            correct_count += 1

    quiz_score = correct_count / total if total > 0 else 0.0

    # ── Update mastery via EMA ────────────────────────────────────────────
    old_mastery = mastery_repository.get_concept_mastery(req.student_id, req.concept)
    new_mastery = old_mastery * 0.7 + quiz_score * 0.3
    new_mastery = round(max(0.0, min(1.0, new_mastery)), 4)
    mastery_repository.upsert_mastery(req.student_id, req.concept, new_mastery)

    # ── Write learning event (thesis evidence, assessment_id as bigint) ───
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
    )
