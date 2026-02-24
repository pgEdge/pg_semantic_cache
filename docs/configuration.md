# Configuration

pg_semantic_cache provides flexible configuration options for vector
dimensions, index types, and cache behavior.

!!! tip "Start Simple"

    When configuring semantic caching, begin with simple defaults (1536 
    dimensions, IVFFlat, 0.95 threshold) and adjust your system based on
    monitoring.

!!! warning "Test Before Production"

    Always test configuration changes in development before applying to
    production!

## Vector Dimensions

The extension supports configurable embedding dimensions to match your
chosen embedding model. pg_semantic_cache supports the following dimensions
and associated models:

| Dimension | Common Models |
|-----------|---------------|
| 768 | BERT, Sentence Transformers (base) |
| 1024 | Sentence Transformers (large) |
| 1536 | OpenAI ada-002, text-embedding-ada-002 |
| 3072 | OpenAI text-embedding-3-large |
| Custom | Any dimension supported by your model |

### Setting Dimensions

!!! warning "Rebuild Required"

    Changing dimensions requires rebuilding the index, which clears all
    cached data.

```sql
-- Set vector dimension (default: 1536)
SELECT semantic_cache.set_vector_dimension(768);

-- Rebuild index to apply changes (WARNING: clears cache)
SELECT semantic_cache.rebuild_index();

-- Verify new dimension
SELECT semantic_cache.get_vector_dimension();
```

### Initial Setup For Custom Dimensions

If you know your embedding model before installation:

```sql
-- Right after CREATE EXTENSION
CREATE EXTENSION pg_semantic_cache;

-- Immediately configure dimensions
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();

-- Now start caching
```

## Vector Index Types

Choose between IVFFlat (fast, approximate) or HNSW (accurate, slower
build).

### IVFFlat Index (Default)

Best for most use cases - fast lookups with good recall.

Characteristics:
- Lookup Speed: Very fast (< 5ms typical)
- Build Time: Fast
- Recall: Good (95%+)
- Memory: Moderate
- Best For: Production caches with frequent updates

```sql
-- Set index type
SELECT semantic_cache.set_index_type('ivfflat');
SELECT semantic_cache.rebuild_index();
```

IVFFlat Parameters (set during `init_schema()`):

```sql
-- Default configuration
lists = 100  -- For < 100K entries

-- For larger caches, increase lists
-- Adjust in the init_schema() function or manually:

DROP INDEX IF EXISTS semantic_cache.idx_cache_entries_embedding;
CREATE INDEX idx_cache_entries_embedding
ON semantic_cache.cache_entries
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 1000);  -- For 100K-1M entries
```

### HNSW Index

More accurate but slower to build - requires pgvector 0.5.0+.

Characteristics:
- Lookup Speed: Fast (1-3ms typical)
- Build Time: Slower
- Recall: Excellent (98%+)
- Memory: Higher
- Best For: Read-heavy caches with infrequent updates

```sql
-- Set index type (requires pgvector 0.5.0+)
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();
```

HNSW Parameters:

```sql
-- Adjust manually for optimal performance

DROP INDEX IF EXISTS semantic_cache.idx_cache_entries_embedding;
CREATE INDEX idx_cache_entries_embedding
ON semantic_cache.cache_entries
USING hnsw (query_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Index Comparison

| Feature | IVFFlat | HNSW |
|---------|---------|------|
| Speed | ⚡⚡⚡ | ⚡⚡ |
| Accuracy | ✓✓ | ✓✓✓ |
| Build Time | ⚡⚡⚡ | ⚡ |
| Memory | 💾 | 💾💾 |
| Updates | Fast | Slower |

## Cache Configuration

The extension stores configuration in the
`semantic_cache.cache_config` table.

### View Current Configuration

Use the following command to view the current configuration:

```sql
SELECT * FROM semantic_cache.cache_config ORDER BY key;
```

### Key Configuration Parameters

Use the following configuration parameters to control cache settings:

#### max_cache_size_mb

Use max_cache_size_mb to specify the maximum cache size in megabytes
before auto-eviction triggers.

```sql
-- Set to 2GB
UPDATE semantic_cache.cache_config
SET value = '2000'
WHERE key = 'max_cache_size_mb';

-- Or default: 1000 MB
```

#### default_ttl_seconds

Use default_ttl_seconds to specify the default time-to-live for cached
entries (can be overridden per query).

```sql
-- Set default to 2 hours
UPDATE semantic_cache.cache_config
SET value = '7200'
WHERE key = 'default_ttl_seconds';

-- Default: 3600 (1 hour)
```

#### eviction_policy

Use eviction_policy to specify the automatic eviction strategy when
cache size limit is reached.

```sql
-- Options: 'lru', 'lfu', 'ttl'
UPDATE semantic_cache.cache_config
SET value = 'lru'
WHERE key = 'eviction_policy';
```

Eviction Policies:

- lru: Least Recently Used - evicts oldest accessed entries
- lfu: Least Frequently Used - evicts least accessed entries
- ttl: Time To Live - evicts entries closest to expiration

#### similarity_threshold

Use similarity_threshold to specify the default similarity threshold for
cache hits (0.0 - 1.0).

```sql
-- More strict matching (fewer hits, more accurate)
UPDATE semantic_cache.cache_config
SET value = '0.98'
WHERE key = 'similarity_threshold';

-- More lenient matching (more hits, less accurate)
UPDATE semantic_cache.cache_config
SET value = '0.90'
WHERE key = 'similarity_threshold';

-- Default: 0.95 (recommended)
```

## Production Configurations

The following sections detail configuration settings useful in a
production environment.

### High-Throughput Configuration

Use the following configuration for applications with thousands of queries
per second:

```sql
-- Use IVFFlat with optimized lists
SELECT semantic_cache.set_index_type('ivfflat');
SELECT semantic_cache.rebuild_index();

-- Increase cache size
UPDATE semantic_cache.cache_config SET value = '5000'
WHERE key = 'max_cache_size_mb';

-- Use LRU for fast eviction
UPDATE semantic_cache.cache_config SET value = 'lru'
WHERE key = 'eviction_policy';

-- Shorter TTL to keep cache fresh
UPDATE semantic_cache.cache_config SET value = '1800'
WHERE key = 'default_ttl_seconds';
```

PostgreSQL settings:
```ini
# postgresql.conf
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 512MB
maintenance_work_mem = 2GB
```

### High-Accuracy Configuration

Use the following configuration for applications requiring maximum precision:

```sql
-- Use HNSW for best recall
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();

-- Strict similarity threshold
UPDATE semantic_cache.cache_config SET value = '0.98'
WHERE key = 'similarity_threshold';

-- Longer TTL for stable results
UPDATE semantic_cache.cache_config SET value = '14400'
WHERE key = 'default_ttl_seconds';
```

### LLM/AI Application Configuration

Use the following configuration settings to optimize caching for expensive AI
API calls:

```sql
-- OpenAI ada-002 dimensions
SELECT semantic_cache.set_vector_dimension(1536);
SELECT semantic_cache.rebuild_index();

-- Balance between accuracy and coverage
UPDATE semantic_cache.cache_config SET value = '0.93'
WHERE key = 'similarity_threshold';

-- Cache longer (AI responses stable)
UPDATE semantic_cache.cache_config SET value = '7200'
WHERE key = 'default_ttl_seconds';

-- Large cache for many queries
UPDATE semantic_cache.cache_config SET value = '10000'
WHERE key = 'max_cache_size_mb';
```

### Analytics Query Configuration

The following configuration is well-suited for caching expensive analytical
queries:

```sql
-- Use standard dimensions
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();

-- Moderate similarity (query variations common)
UPDATE semantic_cache.cache_config SET value = '0.90'
WHERE key = 'similarity_threshold';

-- Short TTL (data changes frequently)
UPDATE semantic_cache.cache_config SET value = '900'
WHERE key = 'default_ttl_seconds';

-- LFU policy (popular queries cached longer)
UPDATE semantic_cache.cache_config SET value = 'lfu'
WHERE key = 'eviction_policy';
```

## Monitoring Configuration Impact

Use the following commands to monitor your semantic cache.

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

Use the following commands to measure lookup performance:

```sql
-- Enable timing
\timing on

-- Test lookup
SELECT * FROM semantic_cache.get_cached_result(
    '[0.1, 0.2, ...]'::text,
    0.95
);
```

Target: < 5ms for most queries

### Cache Hit Rate

Use the following query to monitor cache hit rate:

```sql
-- Monitor hit rate with current config
SELECT * FROM semantic_cache.cache_stats();
```

Target: > 70% for effective caching

### Tuning Checklist

Follow this checklist when tuning your cache configuration:

- Choose a dimension matching your embedding model.
- Select an index type based on workload (IVFFlat for most cases).
- Set a similarity threshold based on accuracy requirements.
- Configure cache size based on available memory.
- Choose an eviction policy matching access patterns.
- Set TTL based on data freshness requirements.
- Monitor hit rate and adjust as needed.

### Common Mistakes

The following common mistakes have simple remediations:

#### Using Wrong Dimensions

```sql
-- Extension configured for 1536, but sending 768-dim
-- vectors
-- Result: Error or poor performance
```

You should use matching model dimensions:

```sql
-- Match your model
SELECT semantic_cache.set_vector_dimension(768);
SELECT semantic_cache.rebuild_index();
```

#### Too Strict Threshold

```sql
UPDATE semantic_cache.cache_config SET value = '0.99'
WHERE key = 'similarity_threshold';
-- Result: Very low hit rate
```

Use a more balanced threshold:

```sql
UPDATE semantic_cache.cache_config SET value = '0.93'
WHERE key = 'similarity_threshold';
-- Allows reasonable variation
```

#### Forgetting To Rebuild

```sql
SELECT semantic_cache.set_vector_dimension(768);
-- Forgot: SELECT semantic_cache.rebuild_index();
-- Result: Old index still in use!
```

Rebuild your cache to use the new index!

## Next Steps

- [Functions Reference](functions/index.md) - Learn about all
  configuration functions.
- [Monitoring](monitoring.md) - Track performance and tune
  configuration.
- [Use Cases](use_cases.md) - See configuration examples in
  practice.
