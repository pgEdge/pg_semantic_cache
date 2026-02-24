# Frequently Asked Questions

## General Questions

### What is semantic caching?

Semantic caching uses vector embeddings to understand the meaning of
queries, not just exact text matching. When you search for "What was Q4
revenue?", the cache can return results for semantically similar queries
like "Show Q4 revenue" or "Q4 revenue please" even though the exact text
is different.

Traditional caching requires exact string matches, while semantic caching
matches based on similarity scores (typically 90-98%).

### Why use pg_semantic_cache instead of a traditional cache like Redis?

Use pg_semantic_cache when:

- Queries are phrased differently but mean the same thing (LLM
  applications, natural language queries).
- You need semantic understanding of query similarity.
- You're already using PostgreSQL and want tight integration.
- You need persistent caching with complex querying capabilities.

Use traditional caching (Redis, Memcached) when:

- You need exact key-value matching.
- Sub-millisecond latency is critical.
- Queries are deterministic and rarely vary.
- You need distributed caching across multiple services.

Use both: pg_semantic_cache for semantic matching + Redis for hot-path
exact matches!

### How does it compare to application-level caching?

The following table compares pg_semantic_cache to application-level
caching:

| Feature | pg_semantic_cache | Application Cache |
|---------|-------------------|-------------------|
| Semantic Matching | Yes | No |
| Database Integration | Native | Requires sync |
| Multi-language | Yes | Per-instance |
| Persistence | Automatic | Manual |
| Vector Operations | Optimized | Not available |
| Shared Across Apps | Yes | No |

### Is it production-ready?

Yes! pg_semantic_cache is production-ready and has the following
characteristics:
- Written in C using stable PostgreSQL APIs
- Tested with PostgreSQL 14-18
- Used in production environments
- Small, focused codebase (~900 lines)
- No complex dependencies (just pgvector)

## Installation & Setup

### Do I need to install pgvector separately?

Yes, pgvector is a required dependency. Install it before
pg_semantic_cache:

```bash
# Install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make && sudo make install

# Then install pg_semantic_cache
cd ../pg_semantic_cache
make && sudo make install
```

### Can I use it with managed PostgreSQL services?

It depends on the service:

- Self-hosted PostgreSQL: Yes
- AWS RDS: Yes (if you can install extensions)
- Azure Database for PostgreSQL: Yes (flexible server)
- Google Cloud SQL: Check extension support
- Supabase: Yes (pgvector supported)
- Neon: Yes (pgvector supported)

Check if your provider supports custom C extensions and pgvector.

### What PostgreSQL versions are supported?

PostgreSQL 14, 15, 16, 17, and 18 are fully supported and tested.

### How do I upgrade the extension?

Use one of the following methods to upgrade the extension:

```sql
-- Drop and recreate (WARNING: clears cache)
DROP EXTENSION pg_semantic_cache CASCADE;
CREATE EXTENSION pg_semantic_cache;

-- Or use ALTER EXTENSION (when upgrade scripts available)
ALTER EXTENSION pg_semantic_cache UPDATE TO '0.4.0';
```

## Performance

### How fast are cache lookups?

Cache lookups are very fast, with the following performance
characteristics:

Target: < 5ms for most queries

Typical Performance:

- IVFFlat index: 2-5ms
- HNSW index: 1-3ms
- Without index: 50-500ms (don't do this!)

Factors affecting speed:

- Cache size (more entries = slightly slower)
- Vector dimension (1536 vs 3072)
- Index type and parameters
- PostgreSQL configuration (work_mem)

```sql
-- Test your lookup speed
\timing on
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
```

### How much storage does it use?

Storage requirements vary based on vector dimensions and result sizes:

Storage per entry:

- Vector embedding: ~6KB (1536 dimensions)
- Result data: Varies (your cached JSONB)
- Metadata: ~200 bytes
- Total: 6KB + your data size

Example:

- 10K entries with 10KB results each = ~160MB
- 100K entries with 5KB results each = ~1.1GB

### What's the maximum cache size?

There's no hard limit, but consider the following practical
considerations:

- < 100K entries: Excellent performance with default settings
- 100K - 1M entries: Increase IVFFlat lists parameter
- > 1M entries: Consider partitioning or HNSW index

Use the following command to configure max size:

```sql
UPDATE semantic_cache.cache_config
SET value = '5000'  -- 5GB
WHERE key = 'max_cache_size_mb';
```

### Does it work with large result sets?

Yes, but consider the following factors:

- Large results (> 1MB) consume more storage
- Serializing/deserializing large JSONB has overhead
- Consider caching aggregated results instead of full datasets

```sql
-- Don't cache this:
SELECT * FROM huge_table;  -- 100MB result

-- Cache this instead:
SELECT COUNT(*), AVG(value), summary_stats
FROM huge_table;  -- 1KB result
```

## Embeddings

### What embedding models can I use?

Any embedding model that produces fixed-dimension vectors:

Popular Models:

- OpenAI text-embedding-ada-002 (1536 dim)
- OpenAI text-embedding-3-small (1536 dim)
- OpenAI text-embedding-3-large (3072 dim)
- Cohere embed-english-v3.0 (1024 dim)
- Sentence Transformers all-MiniLM-L6-v2 (384 dim)
- Sentence Transformers all-mpnet-base-v2 (768 dim)

Use the following commands to configure dimension:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

### Do I need to generate embeddings myself?

Yes. pg_semantic_cache stores and searches embeddings, but doesn't
generate them.

Typical workflow:

1. Generate embedding using your chosen model/API
2. Pass embedding to `cache_query()` or `get_cached_result()`
3. Extension handles similarity search

See [Use Cases](use_cases.md) for integration examples.

### Can I change embedding models later?

Yes, but you need to rebuild the cache:

```sql
-- Change dimension
SELECT semantic_cache.set_vector_dimension(3072);

-- Rebuild (WARNING: clears all cached data)
SELECT semantic_cache.rebuild_index();

-- Re-cache entries with new embeddings
```

### What similarity threshold should I use?

Use the following recommendations to select an appropriate similarity
threshold:

- 0.98-0.99: Nearly identical queries (financial data, strict matching)
- 0.95-0.97: Very similar queries (recommended starting point)
- 0.90-0.94: Similar queries (good for exploratory queries)
- 0.85-0.89: Somewhat related (use with caution)
- < 0.85: Too lenient (likely irrelevant results)

Start with 0.95 and adjust based on your hit rate:

- Hit rate too low? Lower threshold (0.92)
- Getting irrelevant results? Raise threshold (0.97)

## Configuration

### How do I choose between IVFFlat and HNSW?

Choose the index type based on your workload characteristics:

Use IVFFlat (default) when:

- Cache updates frequently
- Build time matters
- < 100K entries
- Good enough recall (95%+)

Use HNSW when:

- Maximum accuracy needed
- Cache mostly read-only
- Have pgvector 0.5.0+
- Can afford slower builds

```sql
-- Switch to HNSW
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();
```

### What TTL should I set?

The TTL depends on your data freshness requirements:

```sql
-- Real-time data (stock prices, weather)
ttl_seconds := 60  -- 1 minute

-- Dynamic data (user dashboards, reports)
ttl_seconds := 1800  -- 30 minutes

-- Semi-static data (analytics, LLM responses)
ttl_seconds := 7200  -- 2 hours

-- Static data (reference data)
ttl_seconds := NULL  -- Never expires
```

### How often should I run maintenance?

Follow this recommended maintenance schedule:

```sql
-- Every 15 minutes: Evict expired entries
SELECT semantic_cache.evict_expired();

-- Every hour: Auto-eviction based on policy
SELECT semantic_cache.auto_evict();

-- Daily: Analyze tables
ANALYZE semantic_cache.cache_entries;
```

Set up with pg_cron:
```sql
SELECT cron.schedule('cache-evict', '*/15 * * * *',
    'SELECT semantic_cache.evict_expired()');
```

## Troubleshooting

### Why is my hit rate so low?

Low hit rates typically have one of the following common causes:

1. Threshold too high
   ```sql
   -- Lower from 0.95 to 0.90
   SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.90);
   ```

2. TTL too short
   ```sql
   -- Check average entry lifetime
   SELECT AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) / 3600
       as avg_age_hours
   FROM semantic_cache.cache_entries;
   ```

3. Poor embedding quality
   - Use better embedding model
   - Ensure consistent embedding generation

4. Cache too small
   ```sql
   -- Check if entries being evicted too quickly
   SELECT * FROM semantic_cache.cache_stats();
   ```

### Cache lookups are returning no results

Use the following debugging steps to troubleshoot this issue:

```sql
-- 1. Check cache has entries
SELECT COUNT(*) FROM semantic_cache.cache_entries;

-- 2. Check for expired entries
SELECT COUNT(*) FROM semantic_cache.cache_entries
WHERE expires_at IS NULL OR expires_at > NOW();

-- 3. Try very low threshold
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.70);

-- 4. Check vector dimension
SELECT semantic_cache.get_vector_dimension();

-- 5. Manually check similarity
SELECT
    query_text,
    (1 - (query_embedding <=> '[...]'::vector)) as similarity
FROM semantic_cache.cache_entries
ORDER BY similarity DESC
LIMIT 5;
```

### Extension won't load

If you encounter the following error:

```sql
ERROR:  could not open extension control file
```

Use this solution:
```bash
# Check installation
ls -l $(pg_config --sharedir)/extension/pg_semantic_cache*

# Reinstall
cd pg_semantic_cache
sudo make install

# Verify pgvector installed
ls -l $(pg_config --pkglibdir)/vector.so
```

### Build errors

If you encounter the following build error:

```bash
fatal error: postgres.h: No such file or directory
```

Use this solution:
```bash
# Debian/Ubuntu
sudo apt-get install postgresql-server-dev-17

# RHEL/Rocky
sudo yum install postgresql17-devel

# macOS
brew install postgresql@17
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
```

### Out of memory errors

If you encounter the following error:

```sql
ERROR:  out of memory
```

Try one of these solutions:

1. Increase work_mem
   ```sql
   SET work_mem = '512MB';
   ```

2. Reduce cache size
   ```sql
   SELECT semantic_cache.evict_lru(5000);  -- Keep only 5K entries
   ```

3. Lower vector dimension
   ```sql
   SELECT semantic_cache.set_vector_dimension(768);  -- Use smaller model
   SELECT semantic_cache.rebuild_index();
   ```

## Best Practices

### Should I cache everything?

No! Cache queries that are:

- Expensive (slow execution)
- Frequently repeated (similar queries)
- Tolerant of slight staleness
- Semantically searchable

Don't cache:

- Simple key-value lookups (use Redis)
- Real-time critical data
- Unique, one-off queries
- Queries that must be current

### How do I test if caching helps?

Use the following approach to measure the performance improvement from
caching:

```sql
-- Measure query time without cache
\timing on
SELECT expensive_query();
-- Time: 450.234 ms

-- With cache (first call - miss)
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
-- Time: 3.456 ms (cache miss) + 450.234 ms (execution)

-- With cache (subsequent calls - hit)
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
-- Time: 3.456 ms (cache hit)

-- Speedup: 450 / 3.5 = 128x faster
```

### Should I use tags?

Yes! Tags are useful for:

- Organization: Group by feature (`ARRAY['dashboard', 'sales']`)
- Bulk invalidation: `invalidate_cache(tag := 'user_123')`
- Analytics: `SELECT * FROM semantic_cache.cache_by_tag`
- Debugging: Find entries by category

```sql
-- Tag everything
SELECT semantic_cache.cache_query(
    query_text,
    embedding,
    result,
    3600,
    ARRAY['app_name', 'feature_name', 'user_id']
);
```


## Still Have Questions?

Contact us through the following channels:

- GitHub Issues: [Report bugs or ask
  questions](https://github.com/pgedge/pg_semantic_cache/issues)
- Discussions: [Community
  discussions](https://github.com/pgedge/pg_semantic_cache/discussions)
