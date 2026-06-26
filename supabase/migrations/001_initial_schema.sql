-- =============================================================================
-- HCAI-ITS — Supabase Initial Schema Migration
-- File: supabase/migrations/001_initial_schema.sql
--
-- Run this once in your Supabase SQL editor (Dashboard → SQL Editor → New Query)
-- or via the Supabase CLI: supabase db push
--
-- Tables (6 exactly as per spec):
--   1. textbook_chunks   — RAG knowledge base with pgvector embeddings
--   2. student_mastery   — per-student per-concept mastery scores
--   3. assessments       — quiz metadata
--   4. assessment_questions — MCQ questions linked to assessments
--   5. learning_events   — quiz attempt history
--   6. messages          — chat message history
-- =============================================================================

-- Enable pgvector extension (required for vector(384) column type)
create extension if not exists vector;

-- =============================================================================
-- 1. textbook_chunks
-- Stores chunked textbook content with 384-dim SentenceTransformer embeddings.
-- The IVFFlat index enables fast approximate cosine similarity search.
-- =============================================================================
create table if not exists textbook_chunks (
    id          bigint generated always as identity primary key,
    page_number integer,
    chunk_index integer,
    content     text not null,
    embedding   vector(384),
    created_at  timestamp default now(),
    -- Natural composite key for upsert (avoids duplicate ingest)
    unique (page_number, chunk_index)
);

-- IVFFlat index for fast approximate nearest neighbour search
-- Use <=> operator (cosine distance) in queries
create index if not exists textbook_chunks_embedding_idx
    on textbook_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- =============================================================================
-- 2. student_mastery
-- Tracks each student's mastery score per concept.
-- EMA update formula: new = (old * 0.7) + (quiz_score * 0.3)
-- =============================================================================
create table if not exists student_mastery (
    id            bigint generated always as identity primary key,
    student_id    uuid not null,
    concept_name  text not null,
    mastery_score numeric(4,2) default 0,
    attempts      integer default 0,
    last_updated  timestamp default now(),
    unique (student_id, concept_name)
);

create index if not exists student_mastery_student_idx on student_mastery (student_id);

-- =============================================================================
-- 3. assessments
-- One row per quiz (e.g., "Variables Quiz").
-- =============================================================================
create table if not exists assessments (
    id           bigint generated always as identity primary key,
    concept_name text not null,
    title        text not null,
    created_at   timestamp default now()
);

create index if not exists assessments_concept_idx on assessments (concept_name);

-- =============================================================================
-- 4. assessment_questions
-- Multiple-choice questions linked to an assessment.
-- correct_answer stores the letter: 'A', 'B', 'C', or 'D'.
-- =============================================================================
create table if not exists assessment_questions (
    id             bigint generated always as identity primary key,
    assessment_id  bigint references assessments(id) on delete cascade,
    question_text  text not null,
    option_a       text not null,
    option_b       text not null,
    option_c       text not null,
    option_d       text not null,
    correct_answer text not null  -- 'A' | 'B' | 'C' | 'D'
);

create index if not exists assessment_questions_assessment_idx
    on assessment_questions (assessment_id);

-- =============================================================================
-- 5. learning_events
-- Records each quiz attempt with score details for analytics.
-- =============================================================================
create table if not exists learning_events (
    id              bigint generated always as identity primary key,
    student_id      uuid not null,
    concept_name    text not null,
    assessment_id   bigint references assessments(id),
    score           numeric(4,2),
    total_questions integer,
    correct_answers integer,
    created_at      timestamp default now()
);

create index if not exists learning_events_student_idx on learning_events (student_id);
create index if not exists learning_events_created_idx on learning_events (created_at desc);

-- =============================================================================
-- 6. messages
-- Chat history between student and AI tutor.
-- role must be 'user' | 'assistant'.
-- =============================================================================
create table if not exists messages (
    id         bigint generated always as identity primary key,
    student_id uuid not null,
    role       text not null check (role in ('user', 'assistant')),
    content    text not null,
    created_at timestamp default now()
);

create index if not exists messages_student_idx on messages (student_id);
create index if not exists messages_created_idx on messages (created_at desc);

-- =============================================================================
-- pgvector RPC: match_chunks
-- Used by retrieval.py to perform cosine similarity search.
-- Call via: supabase.rpc("match_chunks", {...})
-- =============================================================================
create or replace function match_chunks(
    query_embedding vector(384),
    match_threshold float,
    match_count     int
)
returns table (
    id          bigint,
    content     text,
    page_number int,
    chunk_index int,
    similarity  float
)
language sql stable
as $$
    select
        id,
        content,
        page_number,
        chunk_index,
        1 - (embedding <=> query_embedding) as similarity
    from textbook_chunks
    where 1 - (embedding <=> query_embedding) > match_threshold
    order by embedding <=> query_embedding
    limit match_count;
$$;
