# Quick Start

The steps that follow are designed to get you started with semantic caching
quickly and easily. Before using pg_semantic_cache, you must install:

- PostgreSQL 14, 15, 16, 17, or 18
- the pgvector extension
- a C compiler (gcc or clang)
- PostgreSQL development headers

## Installation

Use the following commands to build the extension from the Github
repository:

```bash
# Clone the repository
git clone https://github.com/pgedge/pg_semantic_cache.git
cd pg_semantic_cache

# Build and install
make clean
make
sudo make install
```

After building the extension, you need to install and create the extensions
you'll be using:

```sql
-- Install required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Verify installation
SELECT * FROM semantic_cache.cache_health;
```

### Using pg_semantic_cache

Use the following commands to add a result set to a cache, and then query the
cache with a similar query:

```sql
-- Cache a query result with its embedding
SELECT semantic_cache.cache_query(
    query_text := 'What was our Q4 2024 revenue?',
    query_embedding := '[0.123, 0.456, ...]'::text,  -- From embedding model
    result_data := '{"answer": "Q4 2024 revenue was $2.4M"}'::jsonb,
    ttl_seconds := 1800,  -- 30 minutes
    tags := ARRAY['llm', 'revenue']
);

-- Retrieve with a semantically similar query
SELECT * FROM semantic_cache.get_cached_result(
    query_embedding := '[0.124, 0.455, ...]'::text,  -- Slightly different
    similarity_threshold := 0.95  -- 95% similarity required
);
```

