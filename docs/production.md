# Deploying in a Production Environment

For production environments, optimize PostgreSQL settings and set up automated maintenance.

### PostgreSQL Configuration

Optimize PostgreSQL memory and performance settings for semantic caching workloads.

Optimize PostgreSQL settings for semantic caching workloads:

```sql
-- Memory settings
ALTER SYSTEM SET shared_buffers = '4GB';           -- Adjust based on available RAM
ALTER SYSTEM SET effective_cache_size = '12GB';    -- Typically 50-75% of RAM
ALTER SYSTEM SET work_mem = '256MB';               -- For vector operations

-- Reload configuration
SELECT pg_reload_conf();
```

### Automated Maintenance

Schedule automatic cache maintenance tasks using the pg_cron extension.

Set up automatic cache maintenance using `pg_cron`:

```sql
-- Install pg_cron
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule auto-eviction every 15 minutes
SELECT cron.schedule(
    'semantic-cache-eviction',
    '*/15 * * * *',
    $$SELECT semantic_cache.auto_evict()$$
);

-- Schedule expired entry cleanup every hour
SELECT cron.schedule(
    'semantic-cache-cleanup',
    '0 * * * *',
    $$SELECT semantic_cache.evict_expired()$$
);

-- Verify scheduled jobs
SELECT * FROM cron.job WHERE jobname LIKE 'semantic-cache%';
```

### Index Optimization

Choose the appropriate vector index strategy based on your cache size.

#### Small to Medium Caches (< 100k entries)
Default IVFFlat index works well out of the box.

#### Large Caches (100k - 1M entries)
Increase IVFFlat lists for better performance:

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_embedding;
CREATE INDEX idx_cache_embedding
    ON semantic_cache.cache_entries
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 1000);  -- Increase lists for larger caches
```

#### Very Large Caches (> 1M entries)
Use HNSW index for optimal performance (requires pgvector 0.5.0+):

```sql
DROP INDEX IF EXISTS semantic_cache.idx_cache_embedding;
CREATE INDEX idx_cache_embedding_hnsw
    ON semantic_cache.cache_entries
    USING hnsw (query_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

HNSW provides the following benefits:

- The HNSW index delivers faster queries with 1-2ms response times compared to 3-5ms for IVFFlat.
- HNSW provides better recall accuracy at high similarity thresholds.
- HNSW scales linearly with cache size for consistent performance.

### Monitoring Setup

Set up custom views to monitor cache health and performance metrics.

Create a monitoring dashboard view:

```sql
CREATE OR REPLACE VIEW semantic_cache.production_dashboard AS
SELECT
    (SELECT hit_rate_percent FROM semantic_cache.cache_stats())::numeric(5,2) || '%' as hit_rate,
    (SELECT total_entries FROM semantic_cache.cache_stats()) as total_entries,
    (SELECT pg_size_pretty(SUM(result_size_bytes)::BIGINT) FROM semantic_cache.cache_entries) as cache_size,
    (SELECT COUNT(*) FROM semantic_cache.cache_entries WHERE expires_at <= NOW()) as expired_entries,
    (SELECT value FROM semantic_cache.cache_config WHERE key = 'eviction_policy') as eviction_policy,
    NOW() as snapshot_time;

-- Query the dashboard
SELECT * FROM semantic_cache.production_dashboard;
```

### High Availability Considerations

The cache integrates seamlessly with PostgreSQL's replication and backup mechanisms.

```sql
-- Regular backups of cache metadata (optional)
pg_dump -U postgres -d your_db -t semantic_cache.cache_entries -t semantic_cache.cache_metadata -F c -f cache_backup.dump

-- Replication: Cache data is automatically replicated with PostgreSQL streaming replication
-- No special configuration needed
```

---

---
