-- Setup for volatile query detection demo
-- Uses all-MiniLM-L6-v2 (384-dimensional vectors)

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Initialize cache schema
SELECT semantic_cache.init_schema();

-- The extension was compiled with 384 dims; align config and index to match.
SELECT semantic_cache.set_vector_dimension(384);
SELECT semantic_cache.set_index_type('hnsw');

-- Recreate index using HNSW (works well at any dataset size, no lists tuning needed)
DROP INDEX IF EXISTS semantic_cache.idx_cache_embedding;

ALTER TABLE semantic_cache.cache_entries
    ALTER COLUMN query_embedding TYPE vector(384);

CREATE INDEX idx_cache_embedding ON semantic_cache.cache_entries
    USING hnsw (query_embedding vector_cosine_ops);

-- Separate counter for volatile queries skipped at the application layer.
-- The core extension tracks hits/misses only; volatile skips never reach it.
CREATE TABLE IF NOT EXISTS volatile_stats (
    volatile_skipped INTEGER DEFAULT 0
);
INSERT INTO volatile_stats VALUES (0);

-- Verify
SELECT semantic_cache.get_vector_dimension() AS vector_dimension;
SELECT semantic_cache.get_index_type()       AS index_type;
SELECT * FROM semantic_cache.cache_stats();

SELECT 'Setup complete — pg_semantic_cache ready (384-dim, HNSW)' AS status;
