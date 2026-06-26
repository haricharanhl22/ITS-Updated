-- ============================================================
-- HCAI-ITS Demo Persona Seed Data
-- Run this in Supabase SQL Editor to seed mastery + learning events.
-- Users were created by seed_personas.py:
--   ava_beginner   = student_id 26
--   marcus_inter   = student_id 27
--   priya_advanced = student_id 28
-- ============================================================

-- ── student_mastery ──────────────────────────────────────────

DELETE FROM student_mastery WHERE student_id IN (26, 27, 28);

INSERT INTO student_mastery (student_id, concept_name, mastery_score, attempts, last_updated) VALUES
-- Ava (beginner)
(26, 'Variables',      0.28, 3, now()),
(26, 'Functions',      0.12, 2, now()),
(26, 'Loops',          0.18, 2, now()),
(26, 'OOP',            0.05, 0, now()),
(26, 'Strings',        0.22, 3, now()),
(26, 'Lists',          0.10, 0, now()),
(26, 'Dictionaries',   0.08, 0, now()),
(26, 'Error Handling', 0.04, 0, now()),
-- Marcus (intermediate)
(27, 'Variables',      0.72, 4, now()),
(27, 'Functions',      0.58, 4, now()),
(27, 'Loops',          0.65, 4, now()),
(27, 'OOP',            0.38, 3, now()),
(27, 'Strings',        0.75, 3, now()),
(27, 'Lists',          0.60, 2, now()),
(27, 'Dictionaries',   0.48, 2, now()),
(27, 'Error Handling', 0.42, 0, now()),
-- Priya (advanced)
(28, 'Variables',      0.95, 4, now()),
(28, 'Functions',      0.90, 4, now()),
(28, 'Loops',          0.92, 4, now()),
(28, 'OOP',            0.78, 4, now()),
(28, 'Strings',        0.88, 3, now()),
(28, 'Lists',          0.85, 3, now()),
(28, 'Dictionaries',   0.82, 3, now()),
(28, 'Error Handling', 0.75, 3, now());

-- ── learning_events ──────────────────────────────────────────

DELETE FROM learning_events WHERE student_id IN (26, 27, 28);

INSERT INTO learning_events (student_id, concept_name, score, created_at) VALUES
-- Ava
(26, 'Variables', 0.20, now() - interval '25 days'),
(26, 'Variables', 0.35, now() - interval '22 days'),
(26, 'Variables', 0.45, now() - interval '18 days'),
(26, 'Strings',   0.15, now() - interval '20 days'),
(26, 'Strings',   0.28, now() - interval '15 days'),
(26, 'Strings',   0.30, now() - interval '10 days'),
(26, 'Functions', 0.10, now() - interval '12 days'),
(26, 'Functions', 0.18, now() - interval '8 days'),
(26, 'Loops',     0.20, now() - interval '5 days'),
(26, 'Loops',     0.25, now() - interval '2 days'),
-- Marcus
(27, 'Variables', 0.40, now() - interval '30 days'),
(27, 'Variables', 0.55, now() - interval '25 days'),
(27, 'Variables', 0.65, now() - interval '18 days'),
(27, 'Variables', 0.72, now() - interval '10 days'),
(27, 'Functions', 0.30, now() - interval '28 days'),
(27, 'Functions', 0.45, now() - interval '20 days'),
(27, 'Functions', 0.55, now() - interval '12 days'),
(27, 'Functions', 0.60, now() - interval '5 days'),
(27, 'Loops',     0.38, now() - interval '26 days'),
(27, 'Loops',     0.52, now() - interval '18 days'),
(27, 'Loops',     0.62, now() - interval '10 days'),
(27, 'Loops',     0.68, now() - interval '3 days'),
(27, 'Strings',   0.50, now() - interval '22 days'),
(27, 'Strings',   0.65, now() - interval '14 days'),
(27, 'Strings',   0.72, now() - interval '7 days'),
(27, 'OOP',       0.15, now() - interval '20 days'),
(27, 'OOP',       0.28, now() - interval '12 days'),
(27, 'OOP',       0.38, now() - interval '4 days'),
-- Priya
(28, 'Variables', 0.60, now() - interval '30 days'),
(28, 'Variables', 0.75, now() - interval '22 days'),
(28, 'Variables', 0.88, now() - interval '14 days'),
(28, 'Variables', 0.95, now() - interval '5 days'),
(28, 'Functions', 0.55, now() - interval '28 days'),
(28, 'Functions', 0.70, now() - interval '20 days'),
(28, 'Functions', 0.82, now() - interval '12 days'),
(28, 'Functions', 0.90, now() - interval '4 days'),
(28, 'Loops',     0.58, now() - interval '26 days'),
(28, 'Loops',     0.74, now() - interval '18 days'),
(28, 'Loops',     0.86, now() - interval '10 days'),
(28, 'Loops',     0.92, now() - interval '3 days'),
(28, 'OOP',       0.40, now() - interval '24 days'),
(28, 'OOP',       0.58, now() - interval '16 days'),
(28, 'OOP',       0.70, now() - interval '8 days'),
(28, 'OOP',       0.78, now() - interval '2 days'),
(28, 'Strings',   0.60, now() - interval '22 days'),
(28, 'Strings',   0.76, now() - interval '14 days'),
(28, 'Strings',   0.88, now() - interval '6 days'),
(28, 'Error Handling', 0.45, now() - interval '15 days'),
(28, 'Error Handling', 0.62, now() - interval '8 days'),
(28, 'Error Handling', 0.75, now() - interval '2 days');

SELECT 'Seed complete!' as status,
  (SELECT count(*) FROM student_mastery WHERE student_id IN (26,27,28)) as mastery_rows,
  (SELECT count(*) FROM learning_events  WHERE student_id IN (26,27,28)) as event_rows;
