# Frequently Asked Questions

The FAQ is broken into sections to simplify finding answers to the most
commonly asked questions.

| Section | Description |
|---------|-------------|
| [General Questions](#general-questions) | General semantic caching questions |
| [Installation & Setup](#installation--setup) | Installation and setup concerns |
| [Performance](#performance) | Performance characteristics and optimization |
| [Embeddings](#embeddings) | Embedding models and usage |
| [Configuration](#configuration) | Configuration options and settings |
| [Troubleshooting](#troubleshooting) | Common troubleshooting scenarios |
| [Best Practices](#best-practices) | Best practices for effective usage |

## General Questions

The following sections provide general information about semantic
caching and the pg_semantic_cache extension.

### What is semantic caching?

Semantic caching uses vector embeddings to understand the meaning of
queries, not just exact text matching. When you search for "What was
Q4 revenue?", the cache can return results for semantically similar
queries like "Show Q4 revenue" or "Q4 revenue please" even though
the exact text is different.

Traditional caching requires exact string matches, while semantic
caching matches based on similarity scores (typically 90-98%).

### Why use pg_semantic_cache instead of a traditional cache like Redis?

Use pg_semantic_cache when you need one of the following
capabilities:

- Queries are phrased differently but mean the same thing, such as
  in LLM applications or natural language queries.
- You need semantic understanding of query similarity.
- You are already using PostgreSQL and want tight integration.
- You need persistent caching with complex querying capabilities.

Use traditional caching solutions such as Redis or Memcached when
you need one of the following capabilities:

- You need exact key-value matching.
- Sub-millisecond latency is critical.
- Queries are deterministic and rarely vary.
- You need distributed caching across multiple services.

You can use both pg_semantic_cache for semantic matching and Redis
for hot-path exact matches.

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

Yes, pg_semantic_cache is production-ready and has the following
characteristics:

- The extension is written in C using stable PostgreSQL APIs.
- The extension is tested with PostgreSQL 14-18.
- The extension is used in production environments.
- The extension has a small, focused codebase of about 900 lines.
- The extension has no complex dependencies other than pgvector.

## Installation & Setup

The following sections address common installation and setup
concerns for pg_semantic_cache.

### Do I need to install pgvector separately?

Yes, pgvector is a required dependency. Install it before installing
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

It depends on the service; check if your provider supports custom C
extensions and pgvector:

- Self-hosted PostgreSQL: Yes.
- AWS RDS: Yes, if you can install extensions.
- Azure Database for PostgreSQL: Yes, on flexible server.
- Google Cloud SQL: Check extension support.
- Supabase: Yes, pgvector is supported.
- Neon: Yes, pgvector is supported.

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

The following sections address performance characteristics and
optimization strategies for pg_semantic_cache.

### How fast are cache lookups?

Cache lookups are very fast, with the following performance
characteristics:

Target performance is less than 5ms for most queries.

Typical performance characteristics:

- IVFFlat index: 2-5ms.
- HNSW index: 1-3ms.
- Without index: 50-500ms (not recommended).

Factors affecting speed include the following:

- Cache size, where more entries result in slightly slower lookups.
- Vector dimension, such as 1536 versus 3072.
- Index type and parameters.
- PostgreSQL configuration, particularly work_mem.

In the following example, the `\timing` command measures the lookup
speed:

```sql
\timing on
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
```

### How much storage does it use?

Storage requirements vary based on vector dimensions and result
sizes.

Storage per entry includes the following:

- Vector embedding requires approximately 6KB for 1536 dimensions.
- Result data varies based on your cached JSONB.
- Metadata requires approximately 200 bytes.
- Total storage is 6KB plus your data size.

Example storage requirements:

- 10K entries with 10KB results each require approximately 160MB.
- 100K entries with 5KB results each require approximately 1.1GB.

### What's the maximum cache size?

There is no hard limit, but consider the following practical
considerations:

- Fewer than 100K entries provide excellent performance with
  default settings.
- Between 100K and 1M entries require increasing the IVFFlat lists
  parameter.
- More than 1M entries require considering partitioning or the HNSW
  index.

Use the following command to configure max size:

```sql
UPDATE semantic_cache.cache_config
SET value = '5000'  -- 5GB
WHERE key = 'max_cache_size_mb';
```

### Does it work with large result sets?

Yes, but consider the following factors:

- Large results greater than 1MB consume more storage.
- Serializing and deserializing large JSONB has overhead.
- Consider caching aggregated results instead of full datasets.

In the following example, caching aggregated results instead of full
datasets reduces storage overhead:

```sql
-- Don't cache this:
SELECT * FROM huge_table;

-- Cache this instead:
SELECT COUNT(*), AVG(value), summary_stats
FROM huge_table;
```

## Embeddings

The following sections address embedding models and their use with
pg_semantic_cache.

### What embedding models can I use?

Any embedding model that produces fixed-dimension vectors works with
the extension.

Popular models include the following:

- OpenAI text-embedding-ada-002 with 1536 dimensions.
- OpenAI text-embedding-3-small with 1536 dimensions.
- OpenAI text-embedding-3-large with 3072 dimensions.
- Cohere embed-english-v3.0 with 1024 dimensions.
- Sentence Transformers all-MiniLM-L6-v2 with 384 dimensions.
- Sentence Transformers all-mpnet-base-v2 with 768 dimensions.

Use the following commands to configure dimension:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

### Do I need to generate embeddings myself?

Yes, pg_semantic_cache stores and searches embeddings, but does not
generate them.

The typical workflow includes the following steps:

1. Generate embedding using your chosen model or API.
2. Pass embedding to `cache_query()` or `get_cached_result()`.
3. The extension handles similarity search.

See [Use Cases](use_cases.md) for integration examples.

### Can I change embedding models later?

Yes, but you need to rebuild the cache:

In the following example, changing the vector dimension and
rebuilding the index clears all cached data:

```sql
SELECT semantic_cache.set_vector_dimension(3072);
SELECT semantic_cache.rebuild_index();
```

### What similarity threshold should I use?

Use the following recommendations to select an appropriate similarity
threshold:

- Values from 0.98 to 0.99 match nearly identical queries, suitable
  for financial data or strict matching.
- Values from 0.95 to 0.97 match very similar queries and provide a
  recommended starting point.
- Values from 0.90 to 0.94 match similar queries and work well for
  exploratory queries.
- Values from 0.85 to 0.89 match somewhat related queries and should
  be used with caution.
- Values less than 0.85 are too lenient and likely produce
  irrelevant results.

Start with 0.95 and adjust based on your hit rate by lowering the
threshold to 0.92 if the hit rate is too low, or raising the
threshold to 0.97 if you get irrelevant results.

## Configuration

The following sections address configuration options and settings
for pg_semantic_cache.

### How do I choose between IVFFlat and HNSW?

Choose the index type based on your workload characteristics.

Use IVFFlat (default) when you have one of the following
requirements:

- Cache updates frequently.
- Build time matters.
- Fewer than 100K entries.
- Good enough recall of 95% or higher.

Use HNSW when you have one of the following requirements:

- Maximum accuracy is needed.
- Cache is mostly read-only.
- You have pgvector 0.5.0 or later.
- You can afford slower builds.

In the following example, the `set_index_type` function switches to
the HNSW index:

```sql
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();
```

### What TTL should I set?

The TTL depends on your data freshness requirements.

In the following example, different TTL values are set based on data
freshness requirements:

```sql
-- Real-time data (stock prices, weather)
ttl_seconds := 60

-- Dynamic data (user dashboards, reports)
ttl_seconds := 1800

-- Semi-static data (analytics, LLM responses)
ttl_seconds := 7200

-- Static data (reference data)
ttl_seconds := NULL
```

### How often should I run maintenance?

Follow this recommended maintenance schedule.

In the following example, different maintenance operations run at
scheduled intervals:

```sql
-- Every 15 minutes: Evict expired entries
SELECT semantic_cache.evict_expired();

-- Every hour: Auto-eviction based on policy
SELECT semantic_cache.auto_evict();

-- Daily: Analyze tables
ANALYZE semantic_cache.cache_entries;
```

In the following example, pg_cron schedules the cache eviction:

```sql
SELECT cron.schedule('cache-evict', '*/15 * * * *',
    'SELECT semantic_cache.evict_expired()');
```

## Troubleshooting

The following sections address common troubleshooting scenarios and
their solutions.

### Why is my hit rate so low?

Low hit rates typically have one of the following common causes.

In the following example, lowering the threshold from 0.95 to 0.90
may improve hit rates:

```sql
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.90);
```

In the following example, checking the average entry lifetime helps
determine if TTL is too short:

```sql
SELECT AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) / 3600
    as avg_age_hours
FROM semantic_cache.cache_entries;
```

Poor embedding quality can also cause low hit rates; use a better
embedding model and ensure consistent embedding generation.

In the following example, checking cache statistics helps determine
if the cache is too small:

```sql
SELECT * FROM semantic_cache.cache_stats();
```

### Cache lookups are returning no results

Use the following debugging steps to troubleshoot this issue.

In the following example, checking if the cache has entries is the
first debugging step:

```sql
SELECT COUNT(*) FROM semantic_cache.cache_entries;
```

In the following example, checking for expired entries helps
identify if entries are being evicted:

```sql
SELECT COUNT(*) FROM semantic_cache.cache_entries
WHERE expires_at IS NULL OR expires_at > NOW();
```

In the following example, trying a very low threshold helps
determine if the similarity threshold is too high:

```sql
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.70);
```

In the following example, checking the vector dimension ensures the
embedding dimensions match:

```sql
SELECT semantic_cache.get_vector_dimension();
```

In the following example, manually checking similarity helps
identify the closest matches:

```sql
SELECT
    query_text,
    (1 - (query_embedding <=> '[...]'::vector)) as similarity
FROM semantic_cache.cache_entries
ORDER BY similarity DESC
LIMIT 5;
```

### Extension won't load

If you encounter the following error, the extension control file is
missing:

```sql
ERROR:  could not open extension control file
```

Use this solution to check the installation and reinstall if
necessary:

```bash
ls -l $(pg_config --sharedir)/extension/pg_semantic_cache*

cd pg_semantic_cache
sudo make install

ls -l $(pg_config --pkglibdir)/vector.so
```

### Build errors

If you encounter the following build error, PostgreSQL development
headers are missing:

```bash
fatal error: postgres.h: No such file or directory
```

Use this solution to install the development headers for your
platform:

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

If you encounter the following out of memory error, try one of the
solutions that follow:

```sql
ERROR:  out of memory
```

In the following example, increasing work_mem provides more memory
for vector operations:

```sql
SET work_mem = '512MB';
```

In the following example, reducing cache size by keeping only 5K
entries frees memory:

```sql
SELECT semantic_cache.evict_lru(5000);
```

In the following example, lowering the vector dimension to 768
reduces memory requirements:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

## Best Practices

The following questions provide guidance on best practices for using
pg_semantic_cache effectively.

### Should I cache everything?

No, you should cache queries selectively.

Cache queries that have the following characteristics:

- Expensive queries with slow execution.
- Frequently repeated queries with similar phrasing.
- Queries that are tolerant of slight staleness.
- Queries that are semantically searchable.

Do not cache the following types of queries:

- Simple key-value lookups where Redis is more appropriate.
- Real-time critical data.
- Unique, one-off queries.
- Queries that must return current data.

### How do I test if caching helps?

Use the following approach to measure the performance improvement
from caching.

In the following example, measuring query time without cache
establishes a baseline:

```sql
\timing on
SELECT expensive_query();
```

In the following example, the first call to get_cached_result is a
cache miss and executes the query:

```sql
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
```

In the following example, subsequent calls to get_cached_result are
cache hits and return much faster:

```sql
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.95);
```

### Should I use tags?

Yes, tags are useful for the following purposes:

- Organization allows you to group by feature.
- Bulk invalidation allows you to invalidate all entries with a tag.
- Analytics allows you to query entries by tag.
- Debugging allows you to find entries by category.

In the following example, the `cache_query` function tags entries
with application name, feature name, and user ID:

```sql
SELECT semantic_cache.cache_query(
    query_text,
    embedding,
    result,
    3600,
    ARRAY['app_name', 'feature_name', 'user_id']
);
```


## Still Have Questions?

Review our documentation at the [pgEdge website](https://docs.pgedge.com/).

Contact us through the following channels for additional support:

- Use GitHub Issues to report bugs or ask questions at
  https://github.com/pgedge/pg_semantic_cache/issues
- Use GitHub Discussions for community discussions at
  https://github.com/pgedge/pg_semantic_cache/discussions
