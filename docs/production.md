# Deploying in a Production Environment

For production environments, we recommend that you optimize PostgreSQL
settings and configure automated maintenance. This guide covers
configuration, monitoring, and high availability considerations for
production deployments.

## PostgreSQL Configuration

You should optimize PostgreSQL memory and performance settings for semantic
caching workloads. Proper configuration ensures optimal cache performance
and efficient resource utilization.

In the following example, the `ALTER SYSTEM` commands configure PostgreSQL
memory settings for semantic caching workloads:

```sql
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '256MB';

SELECT pg_reload_conf();
```

Adjust the `shared_buffers` setting based on your available RAM. The
`effective_cache_size` should typically be 50-75% of total RAM. The
`work_mem` setting allocates memory for vector operations.

## Automated Maintenance

You can schedule automatic cache maintenance tasks using the `pg_cron`
extension. Regular maintenance prevents cache bloat and ensures optimal
performance.

In the following example, the `cron.schedule()` function sets up automatic
cache maintenance tasks:

```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    'semantic-cache-eviction',
    '*/15 * * * *',
    $$SELECT semantic_cache.auto_evict()$$
);

SELECT cron.schedule(
    'semantic-cache-cleanup',
    '0 * * * *',
    $$SELECT semantic_cache.evict_expired()$$
);

SELECT * FROM cron.job WHERE jobname LIKE 'semantic-cache%';
```

The first job runs auto-eviction every 15 minutes. The second job removes
expired entries every hour.

## Index Optimization

Choose the appropriate vector index strategy based on your cache size.
Different index types provide optimal performance at different scales.

### Small to Medium Caches

The default IVFFlat index works well for caches with fewer than 100,000
entries. No additional configuration is required for this cache size.

### Large Caches

For caches containing between 100,000 and 1 million entries, increase the
IVFFlat lists parameter for better performance.

In the following example, the `CREATE INDEX` command creates an optimized
IVFFlat index for large caches:

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_embedding;
CREATE INDEX idx_cache_embedding
    ON semantic_cache.cache_entries
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 1000);
```

### Very Large Caches

For caches exceeding 1 million entries, use the HNSW index for optimal
performance. The HNSW index requires pgvector version 0.5.0 or later.

In the following example, the `CREATE INDEX` command creates an HNSW index
for very large caches:

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_embedding;
CREATE INDEX idx_cache_embedding_hnsw
    ON semantic_cache.cache_entries
    USING hnsw (query_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

The HNSW index provides the following benefits:

- The HNSW index delivers faster queries with 1-2ms response times.
- HNSW provides better recall accuracy at high similarity thresholds.
- HNSW scales linearly with cache size for consistent performance.

## Configuring Monitoring

You can configure custom views to monitor cache health and performance
metrics. Regular monitoring helps identify performance issues and optimize
cache configuration.

In the following example, the `CREATE VIEW` command creates a production
monitoring dashboard:

```sql
CREATE OR REPLACE VIEW semantic_cache.production_dashboard AS
SELECT
    (SELECT hit_rate_percent FROM semantic_cache.cache_stats())::NUMERIC(5,2) || '%' AS hit_rate,
    (SELECT total_entries FROM semantic_cache.cache_stats()) AS total_entries,
    (SELECT pg_size_pretty(SUM(result_size_bytes)::BIGINT) FROM semantic_cache.cache_entries) AS cache_size,
    (SELECT COUNT(*) FROM semantic_cache.cache_entries WHERE expires_at <= NOW()) AS expired_entries,
    (SELECT value FROM semantic_cache.cache_config WHERE key = 'eviction_policy') AS eviction_policy,
    NOW() AS snapshot_time;

SELECT * FROM semantic_cache.production_dashboard;
```

## High Availability Considerations

The cache integrates seamlessly with PostgreSQL's replication and backup
mechanisms. The semantic cache data automatically replicates with standard
PostgreSQL streaming replication.

In the following example, the `pg_dump` command creates a backup of cache
metadata:

```bash
pg_dump -U postgres -d your_db \
    -t semantic_cache.cache_entries \
    -t semantic_cache.cache_metadata \
    -F c -f cache_backup.dump
```

The cache data automatically replicates with PostgreSQL streaming
replication. No special configuration is needed for replication.
