-- =============================================================================
-- Migration: 003_generated_quizzes.sql
-- Adds tables for AI-generated (Groq) adaptive quizzes, additive to the existing
-- static `assessments` / `assessment_questions` tables — those are left untouched
-- so the old quiz data model keeps working.
--
-- Run in Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)
-- =============================================================================

-- ── 1. generated_assessments ─────────────────────────────────────────────────
-- One row per quiz ATTEMPT (not per concept) — every time a student opens the
-- quiz, a fresh assessment row + fresh questions are generated.
create table if not exists generated_assessments (
    id           bigint generated always as identity primary key,
    student_id   bigint not null,
    concept_name text   not null,
    difficulty   text   not null check (difficulty in ('easy', 'hard')),
    created_at   timestamptz default now()
);

create index if not exists generated_assessments_student_idx
    on generated_assessments (student_id);

create index if not exists generated_assessments_student_concept_idx
    on generated_assessments (student_id, concept_name, created_at desc);

-- ── 2. generated_questions ───────────────────────────────────────────────────
-- Mirrors assessment_questions' column shape (option_a..d, correct_answer letter)
-- plus an `explanation` column, generated fresh by Groq for each attempt.
create table if not exists generated_questions (
    id             bigint generated always as identity primary key,
    assessment_id  bigint references generated_assessments(id) on delete cascade,
    question_text  text not null,
    option_a       text not null,
    option_b       text not null,
    option_c       text not null,
    option_d       text not null,
    correct_answer text not null check (correct_answer in ('A', 'B', 'C', 'D')),
    explanation    text not null,
    created_at     timestamptz default now()
);

create index if not exists generated_questions_assessment_idx
    on generated_questions (assessment_id);

-- ── 3. learning_events — additive column only ───────────────────────────────
-- Nullable FK so history/analytics can trace a learning event back to the
-- generated_assessment that produced it, without touching the existing
-- `assessment_id` column or any existing rows.
alter table learning_events
    add column if not exists generated_assessment_id bigint
        references generated_assessments(id);

create index if not exists learning_events_generated_assessment_idx
    on learning_events (generated_assessment_id);
