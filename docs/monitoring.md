# Monitoring

This guide provides comprehensive information about monitoring and
optimizing pg_semantic_cache performance.

## Quick Health Check

The following sections describe how to perform a quick health check on
your semantic cache.

In the following example, the `cache_health` view provides an overview
of cache performance metrics:

```sql
SELECT * FROM semantic_cache.cache_health;
```

The query produces output similar to the following example:
```
 total_entries | expired_entries | total_size | avg_access_count | total_hits | total_misses | hit_rate_pct
---------------+-----------------+------------+------------------+------------+--------------+--------------
          1543 |              23 | 145 MB     |            5.78  |       8921 |         2103 |        80.93
```

## Key Metrics

The following sections describe the key metrics for monitoring cache
performance and effectiveness.

### Cache Hit Rate

The cache hit rate is the most important metric for measuring cache
effectiveness.

In the following example, the query calculates the current hit rate
with a rating based on performance thresholds:

```sql
-- Get current hit rate
SELECT
    total_hits,
    total_misses,
    (total_hits + total_misses) as total_queries,
    hit_rate_percent,
    CASE
        WHEN hit_rate_percent >= 80 THEN 'Excellent'
        WHEN hit_rate_percent >= 60 THEN 'Good'
        WHEN hit_rate_percent >= 40 THEN 'Fair'
        ELSE 'Poor'
    END as rating
FROM semantic_cache.cache_stats();
```

The following list shows target hit rates for different use cases:

- LLM and AI applications should achieve 70 to 85 percent hit rates.
- Analytics workloads should achieve 60 to 75 percent hit rates.
- API caching should achieve 75 to 90 percent hit rates.
- Real-time data should achieve 40 to 60 percent hit rates.

### Cache Size and Growth

The cache size and growth metrics help you monitor storage usage and
identify growth trends.

In the following example, the query calculates the current cache size
and entry count statistics:

```sql
SELECT
    COUNT(*) as total_entries,
    pg_size_pretty(SUM(result_size_bytes)::BIGINT) as total_size,
    pg_size_pretty(AVG(result_size_bytes)::BIGINT) as avg_entry_size,
    pg_size_pretty(MAX(result_size_bytes)::BIGINT) as largest_entry,
    pg_size_pretty(MIN(result_size_bytes)::BIGINT) as smallest_entry
FROM semantic_cache.cache_entries;
```

In the following example, the queries create a tracking table and log
cache size over time to identify growth trends:

```sql
CREATE TABLE IF NOT EXISTS monitoring.cache_size_history (
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    entry_count BIGINT,
    total_bytes BIGINT
);
INSERT INTO monitoring.cache_size_history (entry_count, total_bytes)
SELECT COUNT(*), SUM(result_size_bytes)
FROM semantic_cache.cache_entries;

SELECT
    timestamp,
    entry_count,
    pg_size_pretty(total_bytes) as size,
    entry_count - LAG(entry_count) OVER (ORDER BY timestamp)
        as entry_delta,
    pg_size_pretty((total_bytes - LAG(total_bytes)
        OVER (ORDER BY timestamp))::BIGINT) as size_delta
FROM monitoring.cache_size_history
ORDER BY timestamp DESC
LIMIT 20;
```

### Access Patterns

The access pattern metrics help you understand which cache entries are
most valuable to your application.

In the following example, the query identifies the most frequently
accessed cache entries:

```sql
SELECT
    id,
    LEFT(query_text, 60) as query_preview,
    access_count,
    pg_size_pretty(result_size_bytes::BIGINT) as size,
    created_at,
    last_accessed_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours
FROM semantic_cache.cache_entries
ORDER BY access_count DESC
LIMIT 20;
```

In the following example, the query groups cache entries by access
frequency to show the distribution of cache usage:

```sql
SELECT
    CASE
        WHEN access_count = 0 THEN '0 (Never)'
        WHEN access_count BETWEEN 1 AND 5 THEN '1-5 (Low)'
        WHEN access_count BETWEEN 6 AND 20 THEN '6-20 (Medium)'
        WHEN access_count BETWEEN 21 AND 100 THEN '21-100 (High)'
        ELSE '100+ (Very High)'
    END as access_range,
    COUNT(*) as entry_count,
    pg_size_pretty(SUM(result_size_bytes)::BIGINT) as total_size,
    ROUND(AVG(access_count), 2) as avg_accesses
FROM semantic_cache.cache_entries
GROUP BY 1
ORDER BY 1;
```

### Entry Age and Freshness

The entry age metrics help you monitor how old cached entries are and
identify stale data.

In the following example, the query groups cache entries by age to
show the distribution of entry freshness:

```sql
SELECT
    CASE
        WHEN age_minutes < 5 THEN '< 5 min'
        WHEN age_minutes < 30 THEN '5-30 min'
        WHEN age_minutes < 60 THEN '30-60 min'
        WHEN age_minutes < 360 THEN '1-6 hours'
        WHEN age_minutes < 1440 THEN '6-24 hours'
        ELSE '> 24 hours'
    END as age_range,
    COUNT(*) as entry_count,
    pg_size_pretty(SUM(result_size_bytes)::BIGINT) as total_size
FROM (
    SELECT
        EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes,
        result_size_bytes
    FROM semantic_cache.cache_entries
) ages
GROUP BY 1
ORDER BY 1;
```

## Built-in Monitoring Views

The extension provides several built-in views for monitoring cache
performance and health.

### cache_health

The `cache_health` view provides real-time cache health metrics.

In the following example, the query retrieves the current cache health
status:

```sql
SELECT * FROM semantic_cache.cache_health;
```

The view includes:

- the total entries and expired entries.
- the total cache size in megabytes.
- the average access count per entry.
- hit and miss statistics.
- the hit rate percentage.

### recent_cache_activity

The `recent_cache_activity` view shows the most recently accessed cache
entries.

In the following example, the query retrieves the ten most recently
accessed cache entries:

```sql
SELECT * FROM semantic_cache.recent_cache_activity LIMIT 10;
```

The view shows:

- a query preview with the first 80 characters.
- the access count for each entry.
- timestamps for creation, last access, and expiration.
- the result size in bytes.

### cache_by_tag

The `cache_by_tag` view shows cache entries grouped by tag.

In the following example, the query retrieves cache statistics grouped
by tag:

```sql
SELECT * FROM semantic_cache.cache_by_tag;
```

The view is useful for:

- understanding cache composition by feature.
- identifying which features use the cache most.
- planning targeted invalidation strategies.

### cache_access_summary

The `cache_access_summary` view provides hourly access statistics with
cost savings information.

In the following example, the query retrieves hourly access statistics
for the last 24 hours:

```sql
SELECT * FROM semantic_cache.cache_access_summary
ORDER BY hour DESC
LIMIT 24;
```

### cost_savings_daily

The `cost_savings_daily` view provides a daily breakdown of cost
savings from cache hits.

In the following example, the query retrieves daily cost savings for
the last 30 days:

```sql
SELECT * FROM semantic_cache.cost_savings_daily
ORDER BY date DESC
LIMIT 30;
```

### top_cached_queries

The `top_cached_queries` view shows the queries that provide the
greatest cost savings.

In the following example, the query retrieves the ten queries with the
highest cost savings:

```sql
SELECT * FROM semantic_cache.top_cached_queries
LIMIT 10;
```

## Performance Monitoring

The following sections describe how to monitor cache performance and
optimize query execution.

### Query Performance

The query performance metrics help you track how fast cache lookups
execute.

In the following example, the timing is enabled and a cache lookup is
tested with a random embedding vector:

```sql
\timing on

SELECT * FROM semantic_cache.get_cached_result(
    (SELECT array_agg(random()::float4)::text
     FROM generate_series(1, 1536)),
    0.95
);
```

Target performance is less than 5ms for most queries.

In the following example, the benchmark code measures average cache
lookup time over 100 iterations:

```sql
DO $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    test_embedding TEXT;
    i INTEGER;
BEGIN
    -- Generate test embedding
    SELECT array_agg(random()::float4)::text INTO test_embedding
    FROM generate_series(1, 1536);

    -- Run 100 lookups
    start_time := clock_timestamp();

    FOR i IN 1..100 LOOP
        PERFORM * FROM semantic_cache.get_cached_result(test_embedding, 0.95);
    END LOOP;

    end_time := clock_timestamp();

    RAISE NOTICE 'Average lookup time: % ms',
        ROUND((EXTRACT(MILLISECONDS FROM (end_time - start_time))
            / 100)::NUMERIC, 2);
END $$;
```

### Index Performance

The index performance metrics help you monitor vector index
effectiveness and usage.

In the following example, the query checks index usage statistics for
the semantic cache schema:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'semantic_cache'
ORDER BY idx_scan DESC;
```

In the following example, the query retrieves detailed index
statistics including tuples per scan:

```sql
SELECT
    i.indexrelname as index_name,
    t.tablename as table_name,
    pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    ROUND(idx_tup_read::NUMERIC / NULLIF(idx_scan, 0), 2)
        as tuples_per_scan
FROM pg_stat_user_indexes i
JOIN pg_stat_user_tables t ON i.relid = t.relid
WHERE i.schemaname = 'semantic_cache';
```

### PostgreSQL Statistics

The PostgreSQL statistics views provide detailed information about
table and index operations.

In the following example, the query retrieves table statistics for the
semantic cache schema:

```sql
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples
FROM pg_stat_user_tables
WHERE schemaname = 'semantic_cache';
```

## Alerting

The following sections describe how to set up automated alerts for
cache health monitoring.

### Set Up Alerts

The alert function monitors cache health and returns warnings when
metrics fall outside acceptable ranges.

In the following example, the function creates a monitoring alert
system that checks for common cache health issues:

```sql
CREATE OR REPLACE FUNCTION monitoring.check_cache_alerts()
RETURNS TABLE(
    alert_level TEXT,
    alert_type TEXT,
    message TEXT,
    metric_value NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'WARNING'::TEXT,
        'low_hit_rate'::TEXT,
        'Cache hit rate below 60%'::TEXT,
        hit_rate_percent::NUMERIC
    FROM semantic_cache.cache_stats()
    WHERE hit_rate_percent < 60;

    RETURN QUERY
    SELECT
        'WARNING'::TEXT,
        'cache_size'::TEXT,
        'Cache size exceeding 80% of limit'::TEXT,
        (SUM(result_size_bytes) / 1024 / 1024)::NUMERIC
    FROM semantic_cache.cache_entries
    HAVING SUM(result_size_bytes) / 1024 / 1024 > 800;

    RETURN QUERY
    SELECT
        'INFO'::TEXT,
        'expired_entries'::TEXT,
        'More than 10% entries expired'::TEXT,
        COUNT(*)::NUMERIC
    FROM semantic_cache.cache_entries
    WHERE expires_at <= NOW()
    HAVING COUNT(*) > (SELECT COUNT(*) * 0.1
                       FROM semantic_cache.cache_entries);

    RETURN QUERY
    SELECT
        'CRITICAL'::TEXT,
        'no_activity'::TEXT,
        'No cache activity in last hour'::TEXT,
        0::NUMERIC
    FROM semantic_cache.cache_entries
    WHERE last_accessed_at < NOW() - INTERVAL '1 hour'
    HAVING COUNT(*) = (SELECT COUNT(*)
                       FROM semantic_cache.cache_entries);
END;
$$ LANGUAGE plpgsql;

SELECT * FROM monitoring.check_cache_alerts();
```

### Schedule Alert Checks

You can use pg_cron to schedule regular alert checks and notifications.

In the following example, the pg_cron schedule checks for cache alerts
every 15 minutes:

```sql
SELECT cron.schedule(
    'cache-alerts',
    '*/15 * * * *',
    $$
    DO $$
    DECLARE
        alert RECORD;
    BEGIN
        FOR alert IN
            SELECT * FROM monitoring.check_cache_alerts()
        LOOP
            RAISE WARNING '[%] %: % (value: %)',
                alert.alert_level,
                alert.alert_type,
                alert.message,
                alert.metric_value;
        END LOOP;
    END $$;
    $$
);
```

## Integration with Monitoring Tools

The following sections describe how to integrate cache metrics with
external monitoring tools.

### Prometheus and Grafana

You can export cache metrics in Prometheus format for visualization in
Grafana.

In the following example, the function exports cache statistics in
Prometheus text format:

```sql
CREATE OR REPLACE FUNCTION monitoring.prometheus_metrics()
RETURNS TEXT AS $$
DECLARE
    stats RECORD;
    result TEXT := '';
BEGIN
    SELECT * INTO stats FROM semantic_cache.cache_stats();

    result := result || '# HELP cache_entries_total Total entries'
           || E'\n';
    result := result || '# TYPE cache_entries_total gauge' || E'\n';
    result := result || 'cache_entries_total ' || stats.total_entries
           || E'\n';

    result := result || '# HELP cache_hits_total Total cache hits'
           || E'\n';
    result := result || '# TYPE cache_hits_total counter' || E'\n';
    result := result || 'cache_hits_total ' || stats.total_hits || E'\n';

    result := result || '# HELP cache_misses_total Total cache misses'
           || E'\n';
    result := result || '# TYPE cache_misses_total counter' || E'\n';
    result := result || 'cache_misses_total ' || stats.total_misses
           || E'\n';

    result := result || '# HELP cache_hit_rate Cache hit rate percent'
           || E'\n';
    result := result || '# TYPE cache_hit_rate gauge' || E'\n';
    result := result || 'cache_hit_rate ' || stats.hit_rate_percent
           || E'\n';

    RETURN result;
END;
$$ LANGUAGE plpgsql;

SELECT monitoring.prometheus_metrics();
```

### Application Logging

You can integrate cache metrics into your application logging and
monitoring infrastructure.

In the following example, the Python code logs cache metrics to
application logs and optionally sends them to a metrics service:

```python
import psycopg2
import logging

logger = logging.getLogger(__name__)

def log_cache_metrics():
    """Log cache metrics to application logs"""
    conn = psycopg2.connect("dbname=mydb")
    cur = conn.cursor()

    cur.execute("SELECT * FROM semantic_cache.cache_stats()")
    stats = cur.fetchone()

    logger.info(
        "Cache Stats - Entries: %d, Hits: %d, Misses: %d, " +
        "Hit Rate: %.2f%%",
        stats[0], stats[1], stats[2], stats[3]
    )
```

## Optimization Guidelines

The following sections provide guidelines for optimizing cache
performance based on common issues.

### When Hit Rate is Low

If your cache hit rate is below 60 percent, use the following
optimization strategies.

In the following example, the similarity threshold is lowered to 0.90
to allow more cache hits:

```sql
SELECT * FROM semantic_cache.get_cached_result('[...]'::text, 0.90);
```

In the following example, the query checks if entries are expiring too
quickly by calculating the average TTL:

```sql
SELECT COUNT(*), AVG(EXTRACT(EPOCH FROM (expires_at - created_at)))
FROM semantic_cache.cache_entries
WHERE expires_at IS NOT NULL;
```

In the following example, the query examines similarity scores to
verify embedding quality:

```sql
SELECT
    query_text,
    (1 - (query_embedding <=>
          (SELECT query_embedding
           FROM semantic_cache.cache_entries
           LIMIT 1))) as similarity
FROM semantic_cache.cache_entries
ORDER BY similarity DESC
LIMIT 10;
```

### When Cache Size is Growing Too Fast

If your cache is growing faster than expected, use the following
optimization strategies.

In the following example, the TTL is reduced to 30 minutes to expire
entries more quickly:

```sql
UPDATE semantic_cache.cache_config
SET value = '1800'
WHERE key = 'default_ttl_seconds';
```

In the following example, the maximum cache size is reduced and
auto-eviction is triggered:

```sql
UPDATE semantic_cache.cache_config
SET value = '500'
WHERE key = 'max_cache_size_mb';

SELECT semantic_cache.auto_evict();
```

In the following example, entries with zero accesses that are older
than one hour are deleted:

```sql
DELETE FROM semantic_cache.cache_entries
WHERE access_count = 0
  AND created_at < NOW() - INTERVAL '1 hour';
```

### When Lookups are Slow

If cache lookups are taking more than 10ms, use the following
optimization strategies.

In the following example, the IVFFlat index is rebuilt with more lists
for better performance on larger caches:

```sql
DROP INDEX semantic_cache.idx_cache_entries_embedding;
CREATE INDEX idx_cache_entries_embedding
ON semantic_cache.cache_entries
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 1000);
```

In the following example, the index type is switched to HNSW for
better query performance:

```sql
SELECT semantic_cache.set_index_type('hnsw');
SELECT semantic_cache.rebuild_index();
```

In the following example, the work_mem setting is increased to provide
more memory for vector operations:

```sql
SET work_mem = '512MB';
```

## Regular Maintenance Checklist

The following checklist provides recommended maintenance tasks at
different intervals.

Daily tasks include:

- checking the hit rate with `cache_stats` function.
- reviewing the cache size with `cache_health` view.
- clearing expired entries with `evict_expired` function.

Weekly tasks include:

- reviewing top queries with `recent_cache_activity` view.
- checking for alerts with `check_cache_alerts` function.
- analyzing tables with the ANALYZE command.

Monthly tasks include:

- reviewing configuration settings for optimization opportunities.
- optimizing the index if needed based on cache size.
- archiving old access logs to prevent table bloat.
- reviewing cost savings with `get_cost_savings` function.

## See Also

The following resources provide additional information:

- the [Functions Reference](functions/index.md) document describes all
  monitoring functions.
- the [Configuration](configuration.md) document explains tuning
  parameters.
- the [Use Cases](use_cases.md) document provides monitoring patterns
  in practice.
