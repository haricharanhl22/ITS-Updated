"""
backend/seed_data.py
Seed script — inserts 3 sample assessments with 3 MCQs each into Supabase.

Concepts seeded:
  - Variables   (3 questions)
  - Functions   (3 questions)
  - Loops       (3 questions)

Usage:
    cd backend
    python seed_data.py

Requires a valid SUPABASE_URL and SUPABASE_KEY in backend/.env.
If the assessments already exist, this script skips them (idempotent).
"""

import os
import sys
from pathlib import Path

# ── Load .env before importing settings ──────────────────────────────────────
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Manual .env parsing fallback
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# ── Supabase client setup ─────────────────────────────────────────────────────
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Assessment seed data ──────────────────────────────────────────────────────

SEED_DATA = [
    {
        "concept_name": "Variables",
        "title": "Python Variables & Data Types Quiz",
        "questions": [
            {
                "question_text": "Which of the following is a valid variable name in Python?",
                "option_a": "2myvar",
                "option_b": "_my_var",
                "option_c": "my-var",
                "option_d": "my var",
                "correct_answer": "B",
            },
            {
                "question_text": "What is the data type of the value 3.14 in Python?",
                "option_a": "int",
                "option_b": "str",
                "option_c": "float",
                "option_d": "double",
                "correct_answer": "C",
            },
            {
                "question_text": "What does the following code print?\n\nx = 10\ny = x\nx = 20\nprint(y)",
                "option_a": "20",
                "option_b": "10",
                "option_c": "None",
                "option_d": "Error",
                "correct_answer": "B",
            },
        ],
    },
    {
        "concept_name": "Functions",
        "title": "Python Functions Quiz",
        "questions": [
            {
                "question_text": "What keyword is used to define a function in Python?",
                "option_a": "function",
                "option_b": "fun",
                "option_c": "def",
                "option_d": "define",
                "correct_answer": "C",
            },
            {
                "question_text": "What is the output of the following code?\n\ndef greet(name='World'):\n    return f'Hello, {name}!'\n\nprint(greet())",
                "option_a": "Hello, name!",
                "option_b": "Hello, World!",
                "option_c": "Hello, !",
                "option_d": "Error",
                "correct_answer": "B",
            },
            {
                "question_text": "Which of the following creates a lambda function that squares a number?",
                "option_a": "lambda x: x * 2",
                "option_b": "lambda x: x ** 2",
                "option_c": "def square(x): x ** 2",
                "option_d": "function(x) { return x ** 2; }",
                "correct_answer": "B",
            },
        ],
    },
    {
        "concept_name": "Loops",
        "title": "Python Loops Quiz",
        "questions": [
            {
                "question_text": "How many times will the following loop execute?\n\nfor i in range(3):\n    print(i)",
                "option_a": "2",
                "option_b": "4",
                "option_c": "3",
                "option_d": "0",
                "correct_answer": "C",
            },
            {
                "question_text": "Which statement immediately exits a loop in Python?",
                "option_a": "exit",
                "option_b": "stop",
                "option_c": "continue",
                "option_d": "break",
                "correct_answer": "D",
            },
            {
                "question_text": "What is the output of the following code?\n\nresult = [x ** 2 for x in range(4)]\nprint(result)",
                "option_a": "[0, 1, 4, 9]",
                "option_b": "[1, 4, 9, 16]",
                "option_c": "[0, 1, 2, 3]",
                "option_d": "[0, 2, 4, 6]",
                "correct_answer": "A",
            },
        ],
    },
]


# ── Seeding logic ─────────────────────────────────────────────────────────────

def seed():
    print("=" * 60)
    print("HCAI-ITS Seed Script — Assessments + Questions")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL[:40]}...")
    print()

    total_created = 0

    for assessment_data in SEED_DATA:
        concept    = assessment_data["concept_name"]
        title      = assessment_data["title"]
        questions  = assessment_data["questions"]

        # Check if this assessment already exists
        existing = (
            supabase.table("assessments")
            .select("id")
            .eq("concept_name", concept)
            .limit(1)
            .execute()
        )

        if existing.data:
            assessment_id = existing.data[0]["id"]
            print(f"[OK] '{concept}' assessment already exists (id={assessment_id}) - skipping.")
            continue

        # Insert assessment
        result = (
            supabase.table("assessments")
            .insert({"concept_name": concept, "title": title})
            .execute()
        )

        if not result.data:
            print(f"[FAIL] Failed to insert assessment for '{concept}'!")
            continue

        assessment_id = result.data[0]["id"]
        print(f"[OK] Created '{concept}' assessment (id={assessment_id})")

        # Insert questions
        for i, q in enumerate(questions, 1):
            q_row = {**q, "assessment_id": assessment_id}
            q_result = supabase.table("assessment_questions").insert(q_row).execute()
            if q_result.data:
                print(f"   [OK] Question {i}: {q['question_text'][:60]}...")
            else:
                print(f"   [FAIL] Failed to insert question {i} for '{concept}'")

        total_created += 1

    print()
    print("=" * 60)
    if total_created > 0:
        print(f"[SUCCESS] Seeded {total_created} new assessment(s) successfully!")
    else:
        print("[INFO] All assessments already exist. Nothing new was inserted.")
    print()

    # Verify by counting
    count_result = supabase.table("assessments").select("id", count="exact").execute()
    q_count_result = supabase.table("assessment_questions").select("id", count="exact").execute()
    print("Database state:")
    print(f"   assessments:          {count_result.count} rows")
    print(f"   assessment_questions: {q_count_result.count} rows")
    print()


if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"\n[ERROR] Seed script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
