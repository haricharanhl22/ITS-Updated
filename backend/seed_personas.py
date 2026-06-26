"""
backend/seed_personas.py
Seeds 3 demo student accounts with realistic mastery history and learning events.

Run ONCE from the backend/ directory:
    python seed_personas.py

This creates:
  - 3 user accounts: ava_beginner, marcus_inter, priya_advanced
  - Mastery scores across 8 concepts per student
  - Learning events (quiz history) over the past 30 days
"""
import hashlib
import hmac as hmac_mod
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure backend/ is on path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import settings
from supabase import create_client

# Use service key if available (bypasses RLS) — fall back to anon key
_key = getattr(settings, 'supabase_service_key', None) or settings.supabase_key
supabase = create_client(settings.supabase_url, _key)

DEMO_PASSWORD = "DemoPass123!"
_ITERATIONS = 260_000
_SALT_SIZE = 16


def _hash_password(password: str) -> str:
    """Same PBKDF2-SHA256 used in user_repository.py."""
    salt = os.urandom(_SALT_SIZE)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return salt.hex() + ":" + key.hex()


HASHED_PW = _hash_password(DEMO_PASSWORD)

CONCEPTS = ["Variables", "Functions", "Loops", "OOP", "Strings", "Lists", "Dictionaries", "Error Handling"]

PERSONAS = [
    {
        "username": "ava_beginner",
        "email": "ava@demo.hcai-its.local",
        "display_name": "Ava",
        "level": "beginner",
        "mastery": {
            "Variables":      0.28,
            "Functions":      0.12,
            "Loops":          0.18,
            "OOP":            0.05,
            "Strings":        0.22,
            "Lists":          0.10,
            "Dictionaries":   0.08,
            "Error Handling": 0.04,
        },
        # (days_ago, concept, score)
        "events": [
            (25, "Variables", 0.20), (22, "Variables", 0.35), (18, "Variables", 0.45),
            (20, "Strings",   0.15), (15, "Strings",   0.28), (10, "Strings", 0.30),
            (12, "Functions", 0.10), (8,  "Functions", 0.18),
            (5,  "Loops",     0.20), (2,  "Loops",     0.25),
        ],
    },
    {
        "username": "marcus_inter",
        "email": "marcus@demo.hcai-its.local",
        "display_name": "Marcus",
        "level": "intermediate",
        "mastery": {
            "Variables":      0.72,
            "Functions":      0.58,
            "Loops":          0.65,
            "OOP":            0.38,
            "Strings":        0.75,
            "Lists":          0.60,
            "Dictionaries":   0.48,
            "Error Handling": 0.42,
        },
        "events": [
            (30, "Variables", 0.40), (25, "Variables", 0.55), (18, "Variables", 0.65), (10, "Variables", 0.72),
            (28, "Functions", 0.30), (20, "Functions", 0.45), (12, "Functions", 0.55), (5, "Functions", 0.60),
            (26, "Loops",     0.38), (18, "Loops",     0.52), (10, "Loops",     0.62), (3, "Loops", 0.68),
            (22, "Strings",   0.50), (14, "Strings",   0.65), (7, "Strings", 0.72),
            (20, "OOP",       0.15), (12, "OOP",       0.28), (4, "OOP", 0.38),
            (15, "Lists",     0.40), (8, "Lists",      0.55),
            (10, "Dictionaries", 0.30), (5, "Dictionaries", 0.45),
        ],
    },
    {
        "username": "priya_advanced",
        "email": "priya@demo.hcai-its.local",
        "display_name": "Priya",
        "level": "advanced",
        "mastery": {
            "Variables":      0.95,
            "Functions":      0.90,
            "Loops":          0.92,
            "OOP":            0.78,
            "Strings":        0.88,
            "Lists":          0.85,
            "Dictionaries":   0.82,
            "Error Handling": 0.75,
        },
        "events": [
            (30, "Variables", 0.60), (22, "Variables", 0.75), (14, "Variables", 0.88), (5, "Variables", 0.95),
            (28, "Functions", 0.55), (20, "Functions", 0.70), (12, "Functions", 0.82), (4, "Functions", 0.90),
            (26, "Loops",     0.58), (18, "Loops",     0.74), (10, "Loops",     0.86), (3, "Loops", 0.92),
            (24, "OOP",       0.40), (16, "OOP",       0.58), (8, "OOP", 0.70), (2, "OOP", 0.78),
            (22, "Strings",   0.60), (14, "Strings",   0.76), (6, "Strings", 0.88),
            (20, "Lists",     0.55), (12, "Lists",     0.72), (4, "Lists", 0.85),
            (18, "Dictionaries", 0.50), (10, "Dictionaries", 0.68), (3, "Dictionaries", 0.82),
            (15, "Error Handling", 0.45), (8, "Error Handling", 0.62), (2, "Error Handling", 0.75),
        ],
    },
]


def upsert_user(persona: dict) -> int:
    """Create or update the demo user. Returns their database ID."""
    existing = (
        supabase.table("users")
        .select("id")
        .eq("username", persona["username"])
        .limit(1)
        .execute()
    )

    if existing.data:
        uid = existing.data[0]["id"]
        print(f"  User '{persona['username']}' already exists (id={uid})")
        return uid

    result = (
        supabase.table("users")
        .insert({
            "username":        persona["username"],
            "email":           persona["email"],
            "hashed_password": HASHED_PW,
            "role":            "student",
            "is_active":       True,
            "is_verified":     True,
        })
        .execute()
    )
    uid = result.data[0]["id"]
    print(f"  Created user '{persona['username']}' (id={uid})")
    return uid


def seed_mastery(student_id: int, persona: dict):
    """Upsert mastery scores."""
    rows = [
        {
            "student_id":   student_id,
            "concept_name": concept,
            "mastery_score": score,
            "attempts":     len([e for e in persona["events"] if e[1] == concept]),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        for concept, score in persona["mastery"].items()
    ]
    supabase.table("student_mastery").upsert(
        rows, on_conflict="student_id,concept_name"
    ).execute()
    print(f"  Seeded {len(rows)} mastery scores")


def seed_events(student_id: int, persona: dict):
    """Insert historical learning events."""
    now = datetime.now(timezone.utc)

    # First get assessment IDs by concept
    assessments = supabase.table("assessments").select("id, concept_name").execute().data or []
    concept_to_aid = {a["concept_name"]: a["id"] for a in assessments}

    # Delete existing events for this student to avoid duplicates
    supabase.table("learning_events").delete().eq("student_id", student_id).execute()

    rows = []
    for days_ago, concept, score in persona["events"]:
        event_time = now - timedelta(days=days_ago)
        rows.append({
            "student_id":    student_id,
            "concept_name":  concept,
            "assessment_id": concept_to_aid.get(concept),
            "score":         round(score, 4),
            "created_at":    event_time.isoformat(),
        })

    if rows:
        supabase.table("learning_events").insert(rows).execute()
        print(f"  Seeded {len(rows)} learning events")


def main():
    print("[*] Seeding demo personas...\n")
    for persona in PERSONAS:
        print(f"[>] {persona['display_name']} ({persona['level']})")
        uid = upsert_user(persona)
        seed_mastery(uid, persona)
        seed_events(uid, persona)
        print()

    print("[OK] All done! Demo personas are ready.")
    print("\nPersona credentials (used by /demo/login):")
    for p in PERSONAS:
        print(f"  {p['display_name']:10} -> username: {p['username']}, password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
