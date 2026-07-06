-- =============================================================================
-- Migration: 004_quiz_hints.sql
-- Adds LLM-generated per-question hints and hint-usage tracking to the
-- AI-generated quiz flow (generated_assessments / generated_questions).
-- Additive only — the static assessment_questions/assessments tables and the
-- legacy quiz flow are untouched.
--
-- Run in Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
-- =============================================================================

-- ── generated_questions — additive columns ──────────────────────────────────
-- `hint` is nullable because rows generated before this migration have none.
-- `hint_used` defaults false and is flipped to true server-side (submit_quiz)
-- the moment the student reveals the hint for that question in that attempt —
-- since generated_questions is per-attempt (not shared across students), this
-- column can live directly on the row with no cross-student collision risk.
alter table generated_questions
    add column if not exists hint text;

alter table generated_questions
    add column if not exists hint_used boolean not null default false;

-- ── learning_events — additive column ───────────────────────────────────────
-- Aggregate count of hints used in the quiz attempt this event represents.
alter table learning_events
    add column if not exists hints_used_count integer not null default 0;
