-- =============================================================================
-- Migration: 002_add_difficulty_and_concept.sql
-- Adds difficulty level and concept mapping to assessment_questions
-- for the adaptive mastery system.
--
-- Run in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- =============================================================================

-- ── 1. Add difficulty column ────────────────────────────────────────────────
-- 'easy' or 'hard'; existing rows default to 'easy'
ALTER TABLE public.assessment_questions
    ADD COLUMN IF NOT EXISTS difficulty text NOT NULL DEFAULT 'easy'
    CHECK (difficulty IN ('easy', 'hard'));

-- ── 2. Add concept_name column (denormalized for efficient adaptive queries) ─
ALTER TABLE public.assessment_questions
    ADD COLUMN IF NOT EXISTS concept_name text;

-- ── 3. Backfill concept_name from parent assessments table ──────────────────
UPDATE public.assessment_questions aq
SET concept_name = a.concept_name
FROM public.assessments a
WHERE aq.assessment_id = a.id
  AND aq.concept_name IS NULL;

-- Make concept_name NOT NULL after backfill
ALTER TABLE public.assessment_questions
    ALTER COLUMN concept_name SET NOT NULL;

-- ── 4. Indexes for adaptive filtering ───────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_aq_concept_difficulty
    ON public.assessment_questions (concept_name, difficulty);

CREATE INDEX IF NOT EXISTS idx_aq_assessment_difficulty
    ON public.assessment_questions (assessment_id, difficulty);


-- =============================================================================
-- 5. Categorize all existing questions as 'easy'
-- =============================================================================
UPDATE public.assessment_questions
SET difficulty = 'easy'
WHERE difficulty IS NULL OR difficulty = 'easy';


-- =============================================================================
-- 6. INSERT sample HARD questions (2 per concept) for testing
-- =============================================================================

-- ── Hard Variables Questions ────────────────────────────────────────────────
INSERT INTO public.assessment_questions
    (assessment_id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty, concept_name)
VALUES
(
    (SELECT id FROM assessments WHERE concept_name = 'Variables' LIMIT 1),
    E'What is the output of the following code?\n\na = [1, 2, 3]\nb = a\nb.append(4)\nprint(len(a))',
    '3',
    '4',
    'Error',
    'None',
    'B',
    'hard',
    'Variables'
),
(
    (SELECT id FROM assessments WHERE concept_name = 'Variables' LIMIT 1),
    'Which statement about Python variable scoping is correct?',
    'Variables declared in a function are global by default',
    'The `global` keyword creates a new local variable',
    'A nested function can read but not rebind an enclosing variable without `nonlocal`',
    'Python has block-level scoping like Java or C++',
    'C',
    'hard',
    'Variables'
);

-- ── Hard Functions Questions ────────────────────────────────────────────────
INSERT INTO public.assessment_questions
    (assessment_id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty, concept_name)
VALUES
(
    (SELECT id FROM assessments WHERE concept_name = 'Functions' LIMIT 1),
    E'What is the output?\n\ndef make_adder(n):\n    def adder(x):\n        return x + n\n    return adder\n\nadd5 = make_adder(5)\nprint(add5(3))',
    '5',
    '3',
    '8',
    'Error — n is not defined',
    'C',
    'hard',
    'Functions'
),
(
    (SELECT id FROM assessments WHERE concept_name = 'Functions' LIMIT 1),
    E'What happens when a mutable default argument is used?\n\ndef append_to(item, target=[]):\n    target.append(item)\n    return target\n\nprint(append_to(1))\nprint(append_to(2))',
    '[1] then [2]',
    '[1] then [1, 2]',
    'Error on second call',
    '[1, 2] then [1, 2]',
    'B',
    'hard',
    'Functions'
);

-- ── Hard Loops Questions ────────────────────────────────────────────────────
INSERT INTO public.assessment_questions
    (assessment_id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty, concept_name)
VALUES
(
    (SELECT id FROM assessments WHERE concept_name = 'Loops' LIMIT 1),
    E'What is the output of the following generator-based loop?\n\ndef gen():\n    yield 1\n    yield 2\n    yield 3\n\nresult = sum(x**2 for x in gen())\nprint(result)',
    '6',
    '14',
    '9',
    '36',
    'B',
    'hard',
    'Loops'
),
(
    (SELECT id FROM assessments WHERE concept_name = 'Loops' LIMIT 1),
    E'What does this nested comprehension produce?\n\nmatrix = [[1,2],[3,4],[5,6]]\nflat = [x for row in matrix for x in row if x %% 2 == 0]\nprint(flat)',
    '[2, 4, 6]',
    '[1, 3, 5]',
    '[[2], [4], [6]]',
    '[2, 6]',
    'A',
    'hard',
    'Loops'
);


-- =============================================================================
-- 7. Verify — should show easy + hard counts per concept
-- =============================================================================
SELECT concept_name, difficulty, count(*) AS question_count
FROM public.assessment_questions
GROUP BY concept_name, difficulty
ORDER BY concept_name, difficulty;
