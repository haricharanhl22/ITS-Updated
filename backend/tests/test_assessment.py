from __future__ import annotations
from unittest.mock import patch, MagicMock
import pytest

from app.domain.tutor import SubmitRequest
from app.application.assessment_service import submit_assessment


@patch("app.application.assessment_service._get_assessment_row")
@patch("app.application.assessment_service._get_questions")
@patch("app.infrastructure.mastery_repository.get_concept_mastery")
@patch("app.infrastructure.mastery_repository.upsert_mastery")
@patch("app.infrastructure.learning_events_repository.insert_event")
def test_submit_assessment_hard_quiz_perfect_score(
    mock_insert_event,
    mock_upsert_mastery,
    mock_get_concept_mastery,
    mock_get_questions,
    mock_get_assessment_row,
):
    # Setup assessment info
    mock_get_assessment_row.return_value = {"id": 12, "concept_name": "Variables", "title": "Variables Quiz"}

    # Mock DB questions. There are 3 easy and 2 hard questions in the DB.
    db_questions = [
        {"id": 1, "question_text": "Easy 1", "correct_answer": "A", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 2, "question_text": "Easy 2", "correct_answer": "B", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 3, "question_text": "Easy 3", "correct_answer": "C", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 4, "question_text": "Hard 1", "correct_answer": "A", "difficulty": "hard", "concept_name": "Variables"},
        {"id": 5, "question_text": "Hard 2", "correct_answer": "B", "difficulty": "hard", "concept_name": "Variables"},
    ]

    # Mock _get_questions behavior:
    # If filtered by "hard", return the hard questions. If filtered by "easy", return the easy questions.
    def get_questions_mock(assessment_id, difficulty=None):
        if difficulty == "hard":
            return [q for q in db_questions if q["difficulty"] == "hard"]
        elif difficulty == "easy":
            return [q for q in db_questions if q["difficulty"] == "easy"]
        return db_questions

    mock_get_questions.side_effect = get_questions_mock

    # 1. Student with 0.75 mastery (served "hard" questions)
    mock_get_concept_mastery.return_value = 0.75

    # Student answers are for the 2 hard questions (indexed 0 and 1 in the served list)
    # Correct answers are A (0) and B (1)
    req = SubmitRequest(
        student_id=123,
        concept="Variables",
        answers={"0": 0, "1": 1},  # Answers mapped to served indices
    )

    response = submit_assessment(req)

    # Assertions
    assert response.total == 2
    assert response.correct_count == 2
    assert response.score == 1.0
    assert response.new_mastery == 1.0  # Perfect hard quiz must yield 1.0 mastery
    assert response.difficulty_served == "hard"
    mock_upsert_mastery.assert_called_with(123, "Variables", 1.0)


@patch("app.application.assessment_service._get_assessment_row")
@patch("app.application.assessment_service._get_questions")
@patch("app.infrastructure.mastery_repository.get_concept_mastery")
@patch("app.infrastructure.mastery_repository.upsert_mastery")
@patch("app.infrastructure.learning_events_repository.insert_event")
def test_submit_assessment_easy_quiz_perfect_score(
    mock_insert_event,
    mock_upsert_mastery,
    mock_get_concept_mastery,
    mock_get_questions,
    mock_get_assessment_row,
):
    # Setup assessment info
    mock_get_assessment_row.return_value = {"id": 12, "concept_name": "Variables", "title": "Variables Quiz"}

    db_questions = [
        {"id": 1, "question_text": "Easy 1", "correct_answer": "A", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 2, "question_text": "Easy 2", "correct_answer": "B", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 3, "question_text": "Easy 3", "correct_answer": "C", "difficulty": "easy", "concept_name": "Variables"},
        {"id": 4, "question_text": "Hard 1", "correct_answer": "A", "difficulty": "hard", "concept_name": "Variables"},
        {"id": 5, "question_text": "Hard 2", "correct_answer": "B", "difficulty": "hard", "concept_name": "Variables"},
    ]

    def get_questions_mock(assessment_id, difficulty=None):
        if difficulty == "hard":
            return [q for q in db_questions if q["difficulty"] == "hard"]
        elif difficulty == "easy":
            return [q for q in db_questions if q["difficulty"] == "easy"]
        return db_questions

    mock_get_questions.side_effect = get_questions_mock

    # Student with 0.30 mastery (served "easy" questions)
    mock_get_concept_mastery.return_value = 0.30

    # Student answers are for the 3 easy questions (indexed 0, 1, 2 in the served list)
    # Correct answers are A (0), B (1), C (2)
    req = SubmitRequest(
        student_id=123,
        concept="Variables",
        answers={"0": 0, "1": 1, "2": 2},
    )

    response = submit_assessment(req)

    # Assertions
    assert response.total == 3
    assert response.correct_count == 3
    assert response.score == 1.0
    assert response.new_mastery > 0.30  # Mastery must increase
    assert response.new_mastery < 1.0   # Mastery doesn't automatically jump to 1.0 for Easy quiz
    assert response.difficulty_served == "easy"
    mock_upsert_mastery.assert_called_with(123, "Variables", response.new_mastery)
