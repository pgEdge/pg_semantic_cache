# Quick Start

The steps that follow are designed to get you started with semantic
caching quickly and easily. Before using pg_semantic_cache, you must
install the following components:

- PostgreSQL version 14, 15, 16, 17, or 18.
- The pgvector extension.
- A C compiler such as gcc or clang.
- PostgreSQL development headers.

## Installation

Use the following commands to build the extension from the GitHub
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

After building the extension, you need to install and create the
extensions you will be using:

```sql
-- Install required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Verify installation
SELECT * FROM semantic_cache.cache_health;
```

### Using pg_semantic_cache

Use the following commands to add a result set to a cache, and then
query the cache with a similar query:

In the following example, the `cache_query` function stores a query
result with its embedding, and the `get_cached_result` function
retrieves a semantically similar cached result:

```sql
SELECT semantic_cache.cache_query(
    query_text := 'What was our Q4 2024 revenue?',
    query_embedding := '[0.123, 0.456, ...]'::text,
    result_data := '{"answer": "Q4 2024 revenue was $2.4M"}'::jsonb,
    ttl_seconds := 1800,
    tags := ARRAY['llm', 'revenue']
);

SELECT * FROM semantic_cache.get_cached_result(
    query_embedding := '[0.124, 0.455, ...]'::text,
    similarity_threshold := 0.95
);
```

