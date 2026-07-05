"""
backend/app/application/quiz_generation_service.py
AI-generated adaptive quiz service.

Reuses, rather than reimplements:
  - the existing RAG pipeline (app/rag/retrieval.py — SentenceTransformer +
    pgvector `match_chunks`, same as the chat tutor uses)
  - the existing mastery/BKU math (app/application/assessment_service.py —
    _determine_difficulty, _compute_bku_update, _finalize_mastery, and the
    shared MASTERY_THRESHOLD)
  - the existing Groq client construction pattern (mirrors
    app/application/tutor_service.py's _call_groq_sync)

What's new and dedicated to this feature:
  - its own prompt builder (_build_quiz_prompt) — deliberately NOT the tutoring
    prompt, since the task ("produce strict JSON MCQs") is a different contract
  - its own storage: generated_assessments / generated_questions tables via
    app/infrastructure/generated_quiz_repository.py — the static quiz's
    `assessments` / `assessment_questions` tables and assessment_service.py are
    untouched, so the old quiz flow keeps working unmodified.

Flow:
  generate_quiz(student_id, concept):
    1. fetch mastery for the concept -> pick difficulty (same threshold as the
       static quiz)
    2. retrieve textbook chunks for the concept via the existing RAG pipeline
    3. build a dedicated quiz-generation prompt from those chunks only
    4. call Groq; parse + validate the JSON; retry (regenerate) on any
       validation failure up to MAX_GENERATION_ATTEMPTS
    5. persist the assessment + its questions
    6. return the quiz (including correct answers/explanations — see
       GeneratedQuestion in domain/tutor.py for why)

  submit_quiz(student_id, assessment_id, answers):
    1. load the stored assessment + questions, verify ownership
    2. grade every answer against the stored correct_answer
    3. run the identical BKU update + finalize logic used by the static quiz
    4. upsert mastery, insert a learning_events row tagged with this
       generated_assessment_id
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Optional

from groq import RateLimitError

from app.application.assessment_service import (
    _compute_bku_update,
    _determine_difficulty,
    _finalize_mastery,
)
from app.application.tutor_service import CONCEPT_KEYWORDS
from app.config.settings import settings
from app.domain.tutor import GeneratedAssessmentOut, GeneratedQuestion, GeneratedSubmitResponse
from app.infrastructure import generated_quiz_repository, learning_events_repository, mastery_repository
from app.rag.retrieval import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)

_LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}

# Easy quizzes (mastery below threshold) get the full 5-question set; hard
# quizzes (mastery at/above threshold) are shorter, at 2 questions.
QUESTIONS_PER_DIFFICULTY = {"easy": 5, "hard": 2}
MAX_GENERATION_ATTEMPTS = 3

# How many of the student's previous same-concept EASY questions to fetch and
# feed to the HARD-tier prompt as "don't repeat these" context.
PREVIOUS_QUESTIONS_LOOKBACK = 20
_REQUIRED_KEYS = {"question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"}


class QuizGenerationError(Exception):
    """
    Raised when a valid quiz could not be produced (no RAG context available,
    or Groq failed to return a valid quiz after all retries). Callers (api/quiz.py)
    translate this into a client-facing HTTP error.
    """


class QuizRateLimitError(QuizGenerationError):
    """
    Raised when Groq rejects the request with HTTP 429 (rate/quota limit).
    Retrying immediately cannot help — the quota only clears after a cooldown —
    so this is raised straight away instead of burning the remaining retry
    attempts. `retry_after_seconds` is populated when Groq's response exposes it.
    """

    def __init__(self, message: str, retry_after_seconds: Optional[float] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def _extract_retry_after_seconds(exc: Exception) -> Optional[float]:
    """Best-effort extraction of a wait time from a Groq RateLimitError, either
    from a Retry-After response header or from the "try again in 26m42.72s"
    text Groq embeds in the error message."""
    response = getattr(exc, "response", None)
    header = response.headers.get("retry-after") if response is not None else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass

    match = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", str(exc))
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return (int(hours or 0) * 3600) + (int(minutes or 0) * 60) + float(seconds)


# ---------------------------------------------------------------------------
# Concept validation — reuses tutor_service's concept keyword map as the single
# source of truth for "known concepts" instead of inventing a second list.
# ---------------------------------------------------------------------------

def _validate_concept(concept: str) -> None:
    if concept not in CONCEPT_KEYWORDS:
        raise ValueError(
            f"Unknown concept '{concept}'. Valid concepts: {', '.join(CONCEPT_KEYWORDS.keys())}"
        )


# ---------------------------------------------------------------------------
# Dedicated quiz-generation prompt (NOT a reuse of tutor_service._build_prompt —
# a quiz needs strict JSON output, the tutor prompt is free-form prose)
# ---------------------------------------------------------------------------

def _build_quiz_prompt(
    concept: str,
    difficulty: str,
    chunks: list[RetrievedChunk],
    question_count: int,
    avoid_questions: Optional[list[str]] = None,
) -> tuple[str, str]:
    context_section = "\n\n".join(
        f"[Excerpt {i}]\n{chunk.content[:500].strip()}" for i, chunk in enumerate(chunks, 1)
    )

    difficulty_instructions = (
        "Write BEGINNER-level questions: test recall of definitions and basic syntax. "
        "Avoid multi-step reasoning or edge cases."
        if difficulty == "easy" else
        "Write ADVANCED-level questions: test edge cases, subtle behavior, and Pythonic "
        "best practices. Assume the student already knows the basics."
    )

    avoid_section = ""
    if avoid_questions:
        bullet_list = "\n".join(f"- {q}" for q in avoid_questions)
        avoid_section = (
            "\n\nThe student has already been asked these questions in an earlier, easier "
            "quiz on this concept. Do NOT repeat any of them, and do not write close "
            f"rephrasings of them:\n{bullet_list}\n"
        )

    system_prompt = (
        "You are a Python quiz-question generator for an intelligent tutoring system. "
        "You generate multiple-choice questions STRICTLY from the textbook excerpts given "
        "below. Do not use outside knowledge, and do not invent facts unsupported by the "
        "excerpts.\n\n"
        f"Concept: {concept}\n"
        f"Difficulty: {difficulty}. {difficulty_instructions}"
        f"{avoid_section}\n\n"
        "Textbook excerpts (the ONLY source of truth for these questions):\n"
        f"{context_section}\n\n"
        "Requirements:\n"
        f"- Generate EXACTLY {question_count} multiple-choice questions.\n"
        "- Each question has exactly 4 options (A, B, C, D) and exactly one correct answer.\n"
        "- All 4 options within a question must be distinct from each other.\n"
        "- No two questions may be duplicates or near-duplicates of each other.\n"
        "- Every question must be answerable using ONLY the excerpts above.\n"
        "- Include a short (1-2 sentence) explanation of why the correct answer is correct.\n"
        "- Do not leave any field empty.\n\n"
        "Return ONLY valid JSON, with no markdown fences and no commentary, in exactly this "
        "shape:\n"
        '{"questions": [{"question": "...", "option_a": "...", "option_b": "...", '
        '"option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "..."}]}'
    )
    user_prompt = f"Generate the {question_count}-question {difficulty} quiz on {concept} now."
    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Groq call — separate from tutor_service._call_groq_sync: lower temperature
# and JSON response-format mode since output must be machine-parsed, not read.
# ---------------------------------------------------------------------------

def _call_groq_for_quiz(system_prompt: str, user_prompt: str) -> str:
    from groq import Groq

    api_key = settings.groq_api_key
    if not api_key:
        raise QuizGenerationError("GROQ_API_KEY is not set — quiz generation requires Groq.")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=1536,
        top_p=0.9,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Validation (exported for unit testing without hitting Groq/Supabase)
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_json(raw: str) -> dict:
    """Strip ```json fences if the model added them despite instructions not to."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).rstrip("`").strip()
    return json.loads(text)


def _has_history_overlap(questions: list[dict], avoid_questions: list[str]) -> bool:
    """True if any of the freshly-generated `questions` (already cleaned, with
    `question_text`) duplicates one of the student's previously-asked
    `avoid_questions` (raw strings)."""
    avoid_normalized = {_normalize(q) for q in avoid_questions}
    return any(_normalize(q["question_text"]) in avoid_normalized for q in questions)


def validate_and_normalize(raw: str, expected_count: int) -> list[dict]:
    """
    Parse + validate the raw Groq output. Raises ValueError describing the first
    problem found (invalid JSON, wrong question count, missing/empty fields, bad
    correct_answer, duplicate options within a question, duplicate questions
    across the set). Returns question dicts ready for
    generated_quiz_repository.insert_questions().
    """
    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Groq did not return valid JSON: {e}")

    questions = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list) or len(questions) != expected_count:
        got = len(questions) if isinstance(questions, list) else "invalid"
        raise ValueError(f"Expected exactly {expected_count} questions, got {got}")

    seen_question_texts: set[str] = set()
    cleaned: list[dict] = []

    for i, q in enumerate(questions):
        if not isinstance(q, dict) or not _REQUIRED_KEYS.issubset(q.keys()):
            raise ValueError(f"Question {i} is missing required fields")

        for key in _REQUIRED_KEYS:
            if not isinstance(q[key], str) or not q[key].strip():
                raise ValueError(f"Question {i} has an empty or non-string field: {key}")

        correct = q["correct_answer"].strip().upper()
        if correct not in _LETTER_TO_INDEX:
            raise ValueError(f"Question {i} has an invalid correct_answer: {q['correct_answer']!r}")

        options = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
        if len({_normalize(o) for o in options}) != 4:
            raise ValueError(f"Question {i} has duplicate options")

        norm_q = _normalize(q["question"])
        if norm_q in seen_question_texts:
            raise ValueError(f"Question {i} is a duplicate of another question in this quiz")
        seen_question_texts.add(norm_q)

        cleaned.append({
            "question_text": q["question"].strip(),
            "option_a": q["option_a"].strip(),
            "option_b": q["option_b"].strip(),
            "option_c": q["option_c"].strip(),
            "option_d": q["option_d"].strip(),
            "correct_answer": correct,
            "explanation": q["explanation"].strip(),
        })

    return cleaned


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_quiz(student_id: int | str, concept: str) -> GeneratedAssessmentOut:
    """Full pipeline: mastery -> difficulty -> RAG retrieval -> prompt -> Groq
    (validated + retried) -> persist -> return.

    Question count depends on difficulty: 5 for easy, 2 for hard
    (QUESTIONS_PER_DIFFICULTY). For hard quizzes, we also fetch the student's
    previously-asked EASY questions for this concept and ask Groq to avoid
    repeating them — but only the FIRST attempt enforces that; if it still
    overlaps, whatever the next attempt produces is accepted as-is rather than
    looping indefinitely trying to satisfy it.
    """
    _validate_concept(concept)
    sid: int = int(student_id)

    mastery = await asyncio.to_thread(mastery_repository.get_concept_mastery, sid, concept)
    difficulty = _determine_difficulty(mastery)
    question_count = QUESTIONS_PER_DIFFICULTY[difficulty]

    chunks = await retrieve(
        f"{concept} — Python concept explanation, definitions, and examples",
        match_count=5,
        match_threshold=0.20,
    )
    if not chunks:
        raise QuizGenerationError(
            f"No textbook content available for '{concept}'. Ingest a textbook covering "
            f"this concept before generating a quiz (see POST /api/admin/ingest-pdf)."
        )

    avoid_questions: list[str] = []
    if difficulty == "hard":
        avoid_questions = await asyncio.to_thread(
            generated_quiz_repository.get_previous_question_texts,
            sid, concept, "easy", PREVIOUS_QUESTIONS_LOOKBACK,
        )

    system_prompt, user_prompt = _build_quiz_prompt(concept, difficulty, chunks, question_count, avoid_questions)

    questions: Optional[list[dict]] = None
    last_error: Optional[str] = None
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            raw = await asyncio.to_thread(_call_groq_for_quiz, system_prompt, user_prompt)
            candidate = validate_and_normalize(raw, expected_count=question_count)
        except RateLimitError as e:
            # A 429 won't clear within the next few seconds — retrying here would
            # just burn the remaining attempts for nothing. Fail fast instead.
            retry_after = _extract_retry_after_seconds(e)
            wait_msg = f" Please try again in about {round(retry_after / 60)} minute(s)." if retry_after else " Please try again shortly."
            logger.warning(f"Quiz generation hit Groq's rate limit on attempt {attempt}: {e}")
            raise QuizRateLimitError(
                f"The AI quiz generator is temporarily rate-limited by Groq.{wait_msg}",
                retry_after_seconds=retry_after,
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Quiz generation attempt {attempt}/{MAX_GENERATION_ATTEMPTS} failed: {e}")
            continue

        # Structurally valid. On the first attempt only, also require the hard
        # quiz to avoid repeating the student's previous easy questions; from
        # the second attempt onward we stop enforcing that and just accept
        # whatever comes back, so we don't loop forever chasing novelty.
        if attempt == 1 and avoid_questions and _has_history_overlap(candidate, avoid_questions):
            last_error = "Generated questions repeated a previously-asked easy question"
            logger.info(
                f"Hard quiz attempt 1 for '{concept}' (student {sid}) repeated a previous "
                f"easy question; regenerating once more without enforcing novelty."
            )
            continue

        questions = candidate
        break

    if questions is None:
        raise QuizGenerationError(
            f"Could not generate a valid quiz for '{concept}' after "
            f"{MAX_GENERATION_ATTEMPTS} attempts. Last error: {last_error}"
        )

    assessment_id = await asyncio.to_thread(
        generated_quiz_repository.create_assessment, sid, concept, difficulty
    )
    inserted = await asyncio.to_thread(
        generated_quiz_repository.insert_questions, assessment_id, questions
    )

    out_questions = [
        GeneratedQuestion(
            id=i,  # 0-based index for frontend answer-mapping, same convention as the static quiz
            text=row["question_text"],
            options=[row["option_a"], row["option_b"], row["option_c"], row["option_d"]],
            correct_index=_LETTER_TO_INDEX[row["correct_answer"]],
            difficulty=difficulty,
            explanation=row["explanation"],
        )
        for i, row in enumerate(inserted)
    ]

    return GeneratedAssessmentOut(
        assessment_id=assessment_id,
        concept=concept,
        difficulty=difficulty,
        questions=out_questions,
    )


def submit_quiz(student_id: int | str, assessment_id: int, answers: dict[str, int]) -> GeneratedSubmitResponse:
    """
    Grade a generated-quiz attempt server-side against the stored correct answers,
    then apply the SAME BKU update + finalize logic as the static quiz
    (assessment_service._compute_bku_update / _finalize_mastery — not reimplemented).
    """
    sid: int = int(student_id)

    assessment = generated_quiz_repository.get_assessment(assessment_id)
    if not assessment:
        raise ValueError(f"No generated quiz found with id {assessment_id}")
    if int(assessment["student_id"]) != sid:
        raise ValueError("This quiz does not belong to the current student")

    concept = assessment["concept_name"]
    difficulty = assessment["difficulty"]

    rows = generated_quiz_repository.get_questions(assessment_id)
    if not rows:
        raise ValueError(f"Generated quiz {assessment_id} has no questions")

    old_mastery = mastery_repository.get_concept_mastery(sid, concept)
    running_mastery = old_mastery
    correct_count = 0
    total = len(rows)

    for i, row in enumerate(rows):
        correct_index = _LETTER_TO_INDEX[row["correct_answer"]]
        chosen = answers.get(str(i))
        is_correct = chosen is not None and chosen == correct_index
        if is_correct:
            correct_count += 1
        running_mastery = _compute_bku_update(running_mastery, is_correct, difficulty)

    new_mastery = _finalize_mastery(old_mastery, running_mastery, correct_count, total, difficulty)
    quiz_score = correct_count / total if total > 0 else 0.0

    mastery_repository.upsert_mastery(sid, concept, new_mastery)
    learning_events_repository.insert_event(
        student_id=sid,
        concept_name=concept,
        score=quiz_score,
        generated_assessment_id=assessment_id,
    )

    return GeneratedSubmitResponse(
        score=round(quiz_score, 4),
        correct_count=correct_count,
        total=total,
        new_mastery=new_mastery,
        mastery_delta=round(new_mastery - old_mastery, 4),
        difficulty_served=difficulty,
    )
