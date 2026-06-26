-- ============================================================
-- HCAI-ITS pgvector Setup
-- Run this ONCE in Supabase SQL Editor before ingesting lessons.
-- ============================================================

-- 1. Enable pgvector extension (already enabled in Supabase projects by default)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1.5 Create the textbook_chunks table if it doesn't exist
CREATE TABLE IF NOT EXISTS textbook_chunks (
  id BIGSERIAL PRIMARY KEY,
  page_number INT NOT NULL,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(384)
);

-- 2. Add UNIQUE constraint on textbook_chunks so upsert works
ALTER TABLE textbook_chunks
  ADD CONSTRAINT textbook_chunks_page_chunk_unique
  UNIQUE (page_number, chunk_index);

-- 3. Create the cosine similarity search function
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.35,
  match_count     int   DEFAULT 5
)
RETURNS TABLE (
  id          bigint,
  content     text,
  page_number int,
  chunk_index int,
  similarity  float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    content,
    page_number,
    chunk_index,
    1 - (embedding <=> query_embedding) AS similarity
  FROM textbook_chunks
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 4. Index for fast approximate nearest-neighbor search (optional but recommended)
CREATE INDEX IF NOT EXISTS textbook_chunks_embedding_idx
  ON textbook_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 50);

-- Verify the function exists
SELECT routine_name FROM information_schema.routines
WHERE routine_name = 'match_chunks';
