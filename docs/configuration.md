# Configuration

This guide describes how to configure pg_semantic_cache for your use
case, including vector dimensions, index types, and cache behavior.

!!! tip "Start Simple"

    When configuring semantic caching, begin with simple defaults such
    as 1536 dimensions, IVFFlat index, and 0.95 threshold, and adjust
    your system based on monitoring.

!!! warning "Test Before Production"

    Always test configuration changes in development before applying to
    production!

## Vector Dimensions

The extension supports configurable embedding dimensions to match
your chosen embedding model. The pg_semantic_cache extension supports
the following dimensions and associated models:

| Dimension | Common Models |
|-----------|---------------|
| 768 | BERT, Sentence Transformers (base) |
| 1024 | Sentence Transformers (large) |
| 1536 | OpenAI ada-002, text-embedding-ada-002 |
| 3072 | OpenAI text-embedding-3-large |
| Custom | Any dimension supported by your model |

### Setting Dimensions

!!! warning "Rebuild Required"

    Changing dimensions requires rebuilding the index, which clears
    all cached data.

In the following example, the `set_vector_dimension` function changes
the vector dimension to 768, and the `rebuild_index` function applies
the change:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
SELECT semantic_cache.get_vector_dimension();
```

### Initial Setup For Custom Dimensions

If you know your embedding model before installation, configure the
dimensions immediately after creating the extension.

In the following example, the dimensions are set to 768 right after
creating the extension:

```sql
CREATE EXTENSION pg_semantic_cache;
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

## Vector Index Types

Choose between IVFFlat for fast approximate searches or HNSW for
accurate searches with slower build times.

### IVFFlat Index (Default)

The IVFFlat index is best for most use cases and provides fast
lookups with good recall.

The index provides:

- very fast lookups (typically under 5ms).
- fast build times.
- excellent recall (95% or higher).
- moderate memory usage.

This index is best for production caches with frequent updates.

In the following example, the `set_index_type` function sets the
index type to IVFFlat:

```sql
SELECT semantic_cache.set_index_type('ivfflat');
SELECT semantic_cache.rebuild_index();
```

In the following example, the IVFFlat index is configured with 1000
lists for caches with 100K to 1M entries:

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_entries_embedding;
CREATE INDEX idx_cache_entries_embedding
ON semantic_cache.cache_entries
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 1000);
```

### HNSW Index

The HNSW index is more accurate but slower to build and requires
pgvector 0.5.0 or later.

Characteristics include the following:

- Lookup Speed is fast at 1-3ms typically.
- Build Time is slower.
- Recall is excellent at 98% or higher.
- Memory usage is higher.
- Best For read-heavy caches with infrequent updates.

In the following example, the `set_index_type` function sets the
index type to HNSW:

```sql
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();
```

In the following example, the HNSW index is configured with `m=16` and
`ef_construction=64` for optimal performance:

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_entries_embedding;
CREATE INDEX idx_cache_entries_embedding
ON semantic_cache.cache_entries
USING hnsw (query_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Index Comparison

The following table compares the performance characteristics of IVFFlat
and HNSW indexes:

| Feature | IVFFlat | HNSW |
|---------|---------|------|
| Speed | Very Fast | Fast |
| Accuracy | Good | Excellent |
| Build Time | Very Fast | Slow |
| Memory | Moderate | High |
| Updates | Fast | Slower |

## Cache Configuration

The extension stores configuration details in the 
`semantic_cache.cache_config` table.

### View Current Configuration

Use the following command to view the current configuration:

```sql
SELECT * FROM semantic_cache.cache_config ORDER BY key;
```

### Key Configuration Parameters

Use the following configuration parameters to control cache settings.

#### max_cache_size_mb

Use `max_cache_size_mb` to specify the maximum cache size in megabytes
before auto-eviction triggers.

In the following example, the maximum cache size is set to 2GB:

```sql
UPDATE semantic_cache.cache_config
SET value = '2000'
WHERE key = 'max_cache_size_mb';
```

#### default_ttl_seconds

Use `default_ttl_seconds` to specify the default time-to-live for
cached entries, which can be overridden per query.

In the following example, the default TTL is set to 2 hours:

```sql
UPDATE semantic_cache.cache_config
SET value = '7200'
WHERE key = 'default_ttl_seconds';
```

#### eviction_policy

Use eviction_policy to specify the automatic eviction strategy when
the cache size limit is reached.

In the following example, the eviction policy is set to LRU:

```sql
UPDATE semantic_cache.cache_config
SET value = 'lru'
WHERE key = 'eviction_policy';
```

Eviction policies include the following options:

- The lru policy evicts the least recently used entries.
- The lfu policy evicts the least frequently used entries.
- The ttl policy evicts entries closest to expiration.

#### similarity_threshold

Use similarity_threshold to specify the default similarity threshold
for cache hits, with values from 0.0 to 1.0.

In the following example, the similarity threshold is set to 0.98 for
more strict matching:

```sql
UPDATE semantic_cache.cache_config
SET value = '0.98'
WHERE key = 'similarity_threshold';
```

In the following example, the similarity threshold is set to 0.90 for
more lenient matching:

```sql
UPDATE semantic_cache.cache_config
SET value = '0.90'
WHERE key = 'similarity_threshold';
```

## Production Configurations

The following sections detail configuration settings useful in a
production environment.

### High-Throughput Configuration

Use the following configuration options for applications with thousands of
queries per second.

In the following example, the cache is configured for high throughput
with IVFFlat index, large cache size, LRU eviction, and short TTL:

```sql
SELECT semantic_cache.set_index_type('ivfflat');
SELECT semantic_cache.rebuild_index();

UPDATE semantic_cache.cache_config SET value = '5000'
WHERE key = 'max_cache_size_mb';

UPDATE semantic_cache.cache_config SET value = 'lru'
WHERE key = 'eviction_policy';

UPDATE semantic_cache.cache_config SET value = '1800'
WHERE key = 'default_ttl_seconds';
```

In the following example, PostgreSQL is configured with settings
optimized for high throughput:

```ini
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 512MB
maintenance_work_mem = 2GB
```

### High-Accuracy Configuration

Use the following configuration for applications requiring maximum
precision.

In the following example, the cache is configured for high accuracy
with HNSW index, strict similarity threshold, and longer TTL:

```sql
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();

UPDATE semantic_cache.cache_config SET value = '0.98'
WHERE key = 'similarity_threshold';

UPDATE semantic_cache.cache_config SET value = '14400'
WHERE key = 'default_ttl_seconds';
```

### LLM/AI Application Configuration

Use the following configuration settings to optimize caching for
expensive AI API calls.

In the following example, the cache is configured for LLM
applications with OpenAI ada-002 dimensions, balanced threshold, long
TTL, and large cache size:

```sql
SELECT semantic_cache.set_vector_dimension(1536);
SELECT semantic_cache.rebuild_index();

UPDATE semantic_cache.cache_config SET value = '0.93'
WHERE key = 'similarity_threshold';

UPDATE semantic_cache.cache_config SET value = '7200'
WHERE key = 'default_ttl_seconds';

UPDATE semantic_cache.cache_config SET value = '10000'
WHERE key = 'max_cache_size_mb';
```

### Analytics Query Configuration

The following configuration is well-suited for caching expensive
analytical queries.

In the following example, the cache is configured for analytics with
standard dimensions, moderate threshold, short TTL, and LFU policy:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();

UPDATE semantic_cache.cache_config SET value = '0.90'
WHERE key = 'similarity_threshold';

UPDATE semantic_cache.cache_config SET value = '900'
WHERE key = 'default_ttl_seconds';

UPDATE semantic_cache.cache_config SET value = 'lfu'
WHERE key = 'eviction_policy';
```

## Monitoring Configuration Impact

You can use system queries to optimize cache usage.

### Check Index Performance

Use the following query to view index usage statistics:

```sql
-- View index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'semantic_cache';
```

### Measure Lookup Times

Use the following commands to measure lookup performance.

In the following example, the `\timing` command enables timing before
testing lookup performance:

```sql
\timing on
SELECT * FROM semantic_cache.get_cached_result(
    '[0.1, 0.2, ...]'::text,
    0.95
);
```

Target performance is less than 5ms for most queries.

### Cache Hit Rate

Use the following query to monitor cache hit rate.

In the following example, the `cache_stats` function monitors the
cache hit rate:

```sql
SELECT * FROM semantic_cache.cache_stats();
```

Target hit rate is greater than 70% for effective caching.

### Tuning Checklist

Follow this checklist when tuning your cache configuration:

- Choose a dimension matching your embedding model.
- Select an index type based on workload, using IVFFlat for most
  cases.
- Set a similarity threshold based on accuracy requirements.
- Configure cache size based on available memory.
- Choose an eviction policy matching access patterns.
- Set TTL based on data freshness requirements.
- Monitor hit rate and adjust as needed.

### Common Mistakes

The following common mistakes have simple remediations.

#### Using Wrong Dimensions

If the extension is configured for 1536 dimensions but you send 768
dimension vectors, the result is an error or poor performance.

You should use matching model dimensions.

In the following example, the vector dimension is set to match the
model:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

#### Too Strict Threshold

If the similarity threshold is set too high at 0.99, the result is a
very low hit rate.

Use a more balanced threshold.

In the following example, the threshold is set to 0.93 to allow
reasonable variation:

```sql
UPDATE semantic_cache.cache_config SET value = '0.93'
WHERE key = 'similarity_threshold';
```

#### Forgetting To Rebuild

If you set the vector dimension but forget to rebuild the index, the
old index is still in use. You should rebuild your cache to use the new index.

In the following example, the index is rebuilt after changing the
dimension:

```sql
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

