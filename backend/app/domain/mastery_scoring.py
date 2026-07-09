"""
Overall Mastery scoring.

Aggregates per-concept mastery scores into a single curriculum-wide score.
Unlike the raw `student_mastery` table (which only has a row once a concept
has been attempted), every concept here contributes to the result --
unattempted concepts score 0 rather than being excluded from the average.
"""
from app.application.tutor_service import CONCEPT_KEYWORDS

# Per-concept weights for the weighted average, grouped by curriculum tier.
# Higher tiers count for more since they build on the foundational concepts.
# Adding a new concept requires only adding it here (and to CONCEPT_KEYWORDS)
# -- no frontend change needed, since the frontend just displays whatever
# GET /mastery/overall returns.
CONCEPT_WEIGHTS: dict[str, float] = {
    # Tier 1: foundations
    "Variables":      1.0,
    "Strings":        1.0,
    "Lists":          1.0,
    # Tier 2: control flow & structure
    "Loops":          1.5,
    "Functions":      1.5,
    "Dictionaries":   1.5,
    # Tier 3: advanced
    "OOP":            2.0,
    "Error Handling": 2.0,
}

# Keep the weight config honest: every concept the quiz system knows about
# must have a weight, or scoring would silently drop it from the average.
assert set(CONCEPT_KEYWORDS.keys()) == set(CONCEPT_WEIGHTS.keys()), (
    "CONCEPT_WEIGHTS is out of sync with CONCEPT_KEYWORDS -- "
    "every concept must have a configured weight."
)


def compute_overall_mastery(concept_scores: dict[str, float], weighted: bool = True) -> float:
    """
    Compute overall mastery (0.0-1.0) across the entire curriculum.

    concept_scores: mapping of concept name -> mastery score (0.0-1.0) for
    concepts the student has attempted. Concepts absent from this dict are
    treated as 0.0 -- every concept in CONCEPT_WEIGHTS is included in the
    result, attempted or not.
    """
    if weighted:
        total_weight = sum(CONCEPT_WEIGHTS.values())
        if not total_weight:
            return 0.0
        weighted_sum = sum(
            concept_scores.get(concept, 0.0) * weight
            for concept, weight in CONCEPT_WEIGHTS.items()
        )
        return weighted_sum / total_weight

    scores = [concept_scores.get(concept, 0.0) for concept in CONCEPT_WEIGHTS]
    return sum(scores) / len(scores) if scores else 0.0
