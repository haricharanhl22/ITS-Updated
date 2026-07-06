from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from groq import RateLimitError

from app.application.assessment_service import _compute_bku_update, _finalize_mastery
from app.application.quiz_generation_service import (
    QUESTIONS_PER_DIFFICULTY,
    QuizGenerationError,
    QuizRateLimitError,
    _extract_retry_after_seconds,
    generate_quiz,
    validate_and_normalize,
    submit_quiz,
)
from app.rag.retrieval import RetrievedChunk


def _make_rate_limit_error(message: str) -> RateLimitError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code=429, request=request, text=json.dumps({"error": {"message": message}}))
    return RateLimitError(message, response=response, body={"error": {"message": message}})


def _valid_quiz_json(n=5, dup_questions=False, dup_options=False):
    questions = []
    for i in range(n):
        q_text = "What does `len([1,2,3])` return?" if dup_questions else f"Question {i}?"
        options = ["3", "3", "2", "1"] if dup_options else ["3", "2", "1", "0"]
        questions.append({
            "question": q_text,
            "option_a": options[0],
            "option_b": options[1],
            "option_c": options[2],
            "option_d": options[3],
            "correct_answer": "A",
            "explanation": "len() returns the number of items in the list.",
            "hint": "Think about what built-in function counts elements in a sequence.",
        })
    return json.dumps({"questions": questions})


def _quiz_json_with_texts(question_texts):
    """Build a valid quiz JSON payload with specific question texts, so tests
    can control exactly which questions "overlap" a previous-quiz history."""
    questions = [
        {
            "question": text,
            "option_a": "3", "option_b": "2", "option_c": "1", "option_d": "0",
            "correct_answer": "A",
            "explanation": "len() returns the number of items in the list.",
            "hint": "Think about what built-in function counts elements in a sequence.",
        }
        for text in question_texts
    ]
    return json.dumps({"questions": questions})


class TestValidateAndNormalize:
    def test_accepts_a_well_formed_quiz(self):
        cleaned = validate_and_normalize(_valid_quiz_json(), expected_count=5)
        assert len(cleaned) == 5
        assert cleaned[0]["correct_answer"] == "A"
        assert cleaned[0]["question_text"] == "Question 0?"

    def test_accepts_a_two_question_hard_quiz(self):
        cleaned = validate_and_normalize(_valid_quiz_json(n=2), expected_count=2)
        assert len(cleaned) == 2

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{_valid_quiz_json()}\n```"
        cleaned = validate_and_normalize(fenced, expected_count=5)
        assert len(cleaned) == 5

    def test_rejects_invalid_json(self):
        with pytest.raises(ValueError, match="valid JSON"):
            validate_and_normalize("not json at all", expected_count=5)

    def test_rejects_wrong_question_count(self):
        with pytest.raises(ValueError, match="exactly 5"):
            validate_and_normalize(_valid_quiz_json(n=3), expected_count=5)

    def test_rejects_too_many_questions_for_hard_tier(self):
        with pytest.raises(ValueError, match="exactly 2"):
            validate_and_normalize(_valid_quiz_json(n=5), expected_count=2)

    def test_rejects_missing_field(self):
        data = json.loads(_valid_quiz_json())
        del data["questions"][0]["explanation"]
        with pytest.raises(ValueError, match="missing required fields"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_empty_field(self):
        data = json.loads(_valid_quiz_json())
        data["questions"][0]["explanation"] = "   "
        with pytest.raises(ValueError, match="empty"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_bad_correct_answer_letter(self):
        data = json.loads(_valid_quiz_json())
        data["questions"][0]["correct_answer"] = "E"
        with pytest.raises(ValueError, match="invalid correct_answer"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_duplicate_options_within_a_question(self):
        with pytest.raises(ValueError, match="duplicate options"):
            validate_and_normalize(_valid_quiz_json(dup_options=True), expected_count=5)

    def test_rejects_duplicate_questions_across_the_set(self):
        with pytest.raises(ValueError, match="duplicate"):
            validate_and_normalize(_valid_quiz_json(dup_questions=True), expected_count=5)

    def test_rejects_missing_hint(self):
        data = json.loads(_valid_quiz_json())
        del data["questions"][0]["hint"]
        with pytest.raises(ValueError, match="missing required fields"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_empty_hint(self):
        data = json.loads(_valid_quiz_json())
        data["questions"][0]["hint"] = "   "
        with pytest.raises(ValueError, match="empty"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_hint_that_leaks_correct_option_text(self):
        data = json.loads(_valid_quiz_json())
        data["questions"][0]["hint"] = "The answer relates to why the result is 3, the length."
        with pytest.raises(ValueError, match="leaks the correct option"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_rejects_hint_that_names_the_answer_letter(self):
        data = json.loads(_valid_quiz_json())
        data["questions"][0]["hint"] = "Option A is the one you want to pick here."
        with pytest.raises(ValueError, match="reveals the answer letter"):
            validate_and_normalize(json.dumps(data), expected_count=5)

    def test_accepts_a_clean_conceptual_hint(self):
        cleaned = validate_and_normalize(_valid_quiz_json(), expected_count=5)
        assert cleaned[0]["hint"] == "Think about what built-in function counts elements in a sequence."


class TestSubmitQuizReusesExistingMasteryMath:
    """
    submit_quiz must produce IDENTICAL mastery results to assessment_service's
    static-quiz submit_assessment for the same inputs, because both call the
    same _compute_bku_update / _finalize_mastery functions. This test locks
    that reuse in place — if someone reimplements the formula divergently in
    quiz_generation_service.py instead of importing it, this test will drift
    from test_assessment.py's equivalent case.
    """

    @patch("app.application.quiz_generation_service.learning_events_repository.insert_event")
    @patch("app.application.quiz_generation_service.mastery_repository.upsert_mastery")
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_assessment")
    def test_perfect_hard_quiz_snaps_mastery_to_one(
        self,
        mock_get_assessment,
        mock_get_questions,
        mock_get_concept_mastery,
        mock_upsert_mastery,
        mock_insert_event,
    ):
        mock_get_assessment.return_value = {
            "id": 42, "student_id": 7, "concept_name": "Variables", "difficulty": "hard",
        }
        mock_get_questions.return_value = [
            {"correct_answer": "A"},
            {"correct_answer": "B"},
        ]
        mock_get_concept_mastery.return_value = 0.75

        result = submit_quiz(student_id=7, assessment_id=42, answers={"0": 0, "1": 1})

        assert result.total == 2
        assert result.correct_count == 2
        assert result.new_mastery == 1.0
        assert result.difficulty_served == "hard"
        mock_upsert_mastery.assert_called_with(7, "Variables", 1.0)
        mock_insert_event.assert_called_once()
        assert mock_insert_event.call_args.kwargs["generated_assessment_id"] == 42

    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_assessment")
    def test_rejects_submission_for_another_students_quiz(self, mock_get_assessment):
        mock_get_assessment.return_value = {
            "id": 42, "student_id": 7, "concept_name": "Variables", "difficulty": "hard",
        }
        with pytest.raises(ValueError, match="does not belong"):
            submit_quiz(student_id=999, assessment_id=42, answers={"0": 0})

    @patch("app.application.quiz_generation_service.generated_quiz_repository.mark_hints_used")
    @patch("app.application.quiz_generation_service.learning_events_repository.insert_event")
    @patch("app.application.quiz_generation_service.mastery_repository.upsert_mastery")
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_assessment")
    def test_hinted_correct_answer_gets_discounted_gain_and_no_perfect_snap(
        self,
        mock_get_assessment,
        mock_get_questions,
        mock_get_concept_mastery,
        mock_upsert_mastery,
        mock_insert_event,
        mock_mark_hints_used,
    ):
        # Same perfect hard-quiz setup as above, but the student reveals the
        # hint on question 0. A perfect hard quiz would normally snap to 1.0 —
        # using a hint anywhere in the quiz must suppress that and fall back
        # to the (discounted) compounded value instead.
        mock_get_assessment.return_value = {
            "id": 42, "student_id": 7, "concept_name": "Variables", "difficulty": "hard",
        }
        mock_get_questions.return_value = [
            {"id": 101, "correct_answer": "A"},
            {"id": 102, "correct_answer": "B"},
        ]
        mock_get_concept_mastery.return_value = 0.75

        result = submit_quiz(
            student_id=7, assessment_id=42,
            answers={"0": 0, "1": 1},
            hints_used={"0": True},
        )

        assert result.correct_count == 2
        assert result.hints_used_count == 1
        assert result.new_mastery < 1.0   # perfect-score snap must be suppressed
        mock_mark_hints_used.assert_called_once_with([101])
        assert mock_insert_event.call_args.kwargs["hints_used_count"] == 1

    @patch("app.application.quiz_generation_service.generated_quiz_repository.mark_hints_used")
    @patch("app.application.quiz_generation_service.learning_events_repository.insert_event")
    @patch("app.application.quiz_generation_service.mastery_repository.upsert_mastery")
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_assessment")
    def test_hinted_wrong_answer_is_scored_same_as_unhinted_wrong_answer(
        self,
        mock_get_assessment,
        mock_get_questions,
        mock_get_concept_mastery,
        mock_upsert_mastery,
        mock_insert_event,
        mock_mark_hints_used,
    ):
        mock_get_assessment.return_value = {
            "id": 42, "student_id": 7, "concept_name": "Variables", "difficulty": "easy",
        }
        mock_get_questions.return_value = [{"id": 101, "correct_answer": "A"}]
        mock_get_concept_mastery.return_value = 0.5

        hinted = submit_quiz(student_id=7, assessment_id=42, answers={"0": 1}, hints_used={"0": True})

        mock_get_concept_mastery.return_value = 0.5
        unhinted = submit_quiz(student_id=7, assessment_id=42, answers={"0": 1}, hints_used={})

        assert hinted.new_mastery == unhinted.new_mastery
        assert hinted.hints_used_count == 1
        assert unhinted.hints_used_count == 0


class TestBKUHintDiscount:
    """Unit tests for the shared hint-aware BKU math in assessment_service.py."""

    def test_correct_with_hint_gains_half_of_normal_delta(self):
        no_hint = _compute_bku_update(0.5, is_correct=True, difficulty="easy", hint_used=False)
        with_hint = _compute_bku_update(0.5, is_correct=True, difficulty="easy", hint_used=True)
        assert with_hint - 0.5 == pytest.approx((no_hint - 0.5) * 0.5)

    def test_wrong_with_hint_is_unaffected(self):
        no_hint = _compute_bku_update(0.5, is_correct=False, difficulty="easy", hint_used=False)
        with_hint = _compute_bku_update(0.5, is_correct=False, difficulty="easy", hint_used=True)
        assert no_hint == with_hint

    def test_any_hint_used_suppresses_hard_perfect_snap(self):
        result = _finalize_mastery(0.75, 0.82, correct_count=2, total=2, difficulty_served="hard", any_hint_used=True)
        assert result == 0.82
        assert result != 1.0

    def test_any_hint_used_suppresses_easy_perfect_floor(self):
        result = _finalize_mastery(0.5, 0.45, correct_count=3, total=3, difficulty_served="easy", any_hint_used=True)
        # Without hints this would floor at max(old, running) == 0.5; with a
        # hint used, the plain compounded value is kept instead.
        assert result == 0.45

    def test_no_hint_used_keeps_existing_perfect_score_behaviour(self):
        assert _finalize_mastery(0.75, 0.82, correct_count=2, total=2, difficulty_served="hard") == 1.0


class TestExtractRetryAfterSeconds:
    def test_parses_hours_minutes_seconds_from_groq_message(self):
        err = _make_rate_limit_error("Rate limit reached. Please try again in 1h2m3.5s.")
        assert _extract_retry_after_seconds(err) == pytest.approx(3723.5)

    def test_parses_minutes_and_seconds_only(self):
        err = _make_rate_limit_error("Please try again in 26m42.72s")
        assert _extract_retry_after_seconds(err) == pytest.approx(1602.72)

    def test_returns_none_when_unparseable(self):
        err = _make_rate_limit_error("Rate limit reached, no wait time given.")
        assert _extract_retry_after_seconds(err) is None


class TestGenerateQuizFailsFastOnRateLimit:
    """
    A 429 from Groq must NOT be retried like a validation failure — the quota
    won't clear within the next couple of seconds, so retrying 3x just wastes
    calls and delays a response the user can't do anything about anyway.
    """

    @patch("app.application.quiz_generation_service._call_groq_for_quiz")
    @patch("app.application.quiz_generation_service.retrieve", new_callable=AsyncMock)
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    def test_raises_quiz_rate_limit_error_after_a_single_attempt(
        self, mock_get_concept_mastery, mock_retrieve, mock_call_groq
    ):
        mock_get_concept_mastery.return_value = 0.3
        mock_retrieve.return_value = [
            RetrievedChunk(id=1, content="A variable stores a value.", page_number=1, chunk_index=0, similarity=0.9)
        ]
        mock_call_groq.side_effect = _make_rate_limit_error(
            "Rate limit reached for model. Please try again in 26m42.72s."
        )

        with pytest.raises(QuizRateLimitError) as exc_info:
            asyncio.run(generate_quiz(student_id=1, concept="Variables"))

        assert mock_call_groq.call_count == 1  # no wasted retries
        assert exc_info.value.retry_after_seconds == pytest.approx(1602.72)
        assert "rate-limited" in str(exc_info.value)


class TestQuestionCountByDifficulty:
    def test_easy_is_five_and_hard_is_two(self):
        assert QUESTIONS_PER_DIFFICULTY == {"easy": 5, "hard": 2}


class TestGenerateQuizEasyTierSkipsHistoryLookup:
    """Easy quizzes (mastery below threshold) should request 5 questions and
    never bother fetching previous-question history — that history lookup
    only matters for hard-tier generation."""

    @patch("app.application.quiz_generation_service.generated_quiz_repository.insert_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.create_assessment")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_previous_question_texts")
    @patch("app.application.quiz_generation_service._call_groq_for_quiz")
    @patch("app.application.quiz_generation_service.retrieve", new_callable=AsyncMock)
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    def test_requests_five_questions_and_skips_history(
        self,
        mock_get_mastery,
        mock_retrieve,
        mock_call_groq,
        mock_get_previous,
        mock_create_assessment,
        mock_insert_questions,
    ):
        mock_get_mastery.return_value = 0.2  # below threshold -> easy
        mock_retrieve.return_value = [
            RetrievedChunk(id=1, content="A variable stores a value.", page_number=1, chunk_index=0, similarity=0.9)
        ]
        mock_call_groq.return_value = _valid_quiz_json(n=5)
        mock_create_assessment.return_value = 100
        mock_insert_questions.return_value = validate_and_normalize(_valid_quiz_json(n=5), expected_count=5)

        result = asyncio.run(generate_quiz(student_id=1, concept="Variables"))

        mock_get_previous.assert_not_called()
        assert mock_call_groq.call_count == 1
        assert len(result.questions) == 5
        assert result.difficulty == "easy"


class TestGenerateQuizHardTierAvoidsHistoryOnFirstAttemptOnly:
    """
    Hard quizzes (mastery at/above threshold) request only 2 questions, and try
    once to avoid repeating a question already asked in an earlier easy quiz.
    If the very next attempt still overlaps, it must be accepted anyway rather
    than retried indefinitely.
    """

    @patch("app.application.quiz_generation_service.generated_quiz_repository.insert_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.create_assessment")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_previous_question_texts")
    @patch("app.application.quiz_generation_service._call_groq_for_quiz")
    @patch("app.application.quiz_generation_service.retrieve", new_callable=AsyncMock)
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    def test_regenerates_once_then_accepts_remaining_overlap(
        self,
        mock_get_mastery,
        mock_retrieve,
        mock_call_groq,
        mock_get_previous,
        mock_create_assessment,
        mock_insert_questions,
    ):
        mock_get_mastery.return_value = 0.9  # at/above threshold -> hard
        mock_retrieve.return_value = [
            RetrievedChunk(id=1, content="Functions are defined with def.", page_number=1, chunk_index=0, similarity=0.9)
        ]
        mock_get_previous.return_value = ["What keyword defines a function?"]

        first_attempt = _quiz_json_with_texts([
            "What keyword defines a function?",  # duplicates history -> must regenerate
            "How do you call a function?",
        ])
        second_attempt = _quiz_json_with_texts([
            "What keyword defines a function?",  # STILL duplicates -> must be accepted anyway
            "What does `return` do?",
        ])
        mock_call_groq.side_effect = [first_attempt, second_attempt]
        mock_create_assessment.return_value = 99
        mock_insert_questions.return_value = validate_and_normalize(second_attempt, expected_count=2)

        result = asyncio.run(generate_quiz(student_id=1, concept="Functions"))

        mock_get_previous.assert_called_once_with(1, "Functions", "easy", 20)
        assert mock_call_groq.call_count == 2  # regenerated exactly once, then stopped
        assert len(result.questions) == 2
        assert result.difficulty == "hard"

    @patch("app.application.quiz_generation_service.generated_quiz_repository.insert_questions")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.create_assessment")
    @patch("app.application.quiz_generation_service.generated_quiz_repository.get_previous_question_texts")
    @patch("app.application.quiz_generation_service._call_groq_for_quiz")
    @patch("app.application.quiz_generation_service.retrieve", new_callable=AsyncMock)
    @patch("app.application.quiz_generation_service.mastery_repository.get_concept_mastery")
    def test_accepts_first_attempt_immediately_when_no_overlap(
        self,
        mock_get_mastery,
        mock_retrieve,
        mock_call_groq,
        mock_get_previous,
        mock_create_assessment,
        mock_insert_questions,
    ):
        mock_get_mastery.return_value = 0.9
        mock_retrieve.return_value = [
            RetrievedChunk(id=1, content="Functions are defined with def.", page_number=1, chunk_index=0, similarity=0.9)
        ]
        mock_get_previous.return_value = ["What keyword defines a function?"]

        fresh_attempt = _quiz_json_with_texts([
            "How many parameters can a function take?",
            "What does `return` do?",
        ])
        mock_call_groq.return_value = fresh_attempt
        mock_create_assessment.return_value = 101
        mock_insert_questions.return_value = validate_and_normalize(fresh_attempt, expected_count=2)

        result = asyncio.run(generate_quiz(student_id=1, concept="Functions"))

        assert mock_call_groq.call_count == 1  # no unnecessary regeneration
        assert len(result.questions) == 2
