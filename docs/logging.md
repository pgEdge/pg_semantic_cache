# Logging and Cost Tracking

This guide describes how to track cache hits and misses and calculate
cost savings from avoided LLM API calls.

The following sections provide a quick introduction to logging cache
access and tracking cost savings.

In the following example, the `log_cache_access` function logs cache
access events and retrieves cost savings reports:

```sql
SELECT semantic_cache.log_cache_access('query_hash', false, NULL, 0.006);

SELECT semantic_cache.log_cache_access('query_hash', true, 0.95, 0.006);

SELECT * FROM semantic_cache.get_cost_savings(7);

SELECT * FROM semantic_cache.cost_savings_daily
ORDER BY date DESC
LIMIT 7;
```

## Functions

The following sections describe the functions available for logging
cache access and calculating cost savings.

### log_cache_access

The `log_cache_access` function records a cache access event with cost
information.

In the following example, the function signature shows the required
parameters for logging cache access:

```sql
SELECT semantic_cache.log_cache_access(
    query_hash text,
    cache_hit boolean,
    similarity_score float4,
    query_cost numeric
);
```

In the following example, the function logs a cache miss when the LLM
API must be called:

```sql
SELECT semantic_cache.log_cache_access('abc123...', false, NULL, 0.008);
```

In the following example, the function logs a cache hit when a cached
result is returned:

```sql
SELECT semantic_cache.log_cache_access('def456...', true, 0.97, 0.008);
```

### get_cost_savings

The `get_cost_savings` function generates a cost savings report for a
specified time period.

In the following example, the function signature shows the optional
days parameter defaulting to 30:

```sql
SELECT * FROM semantic_cache.get_cost_savings(
    days integer DEFAULT 30
);
```

The following table describes the columns returned by the function:

| Column | Type | Description |
|--------|------|-------------|
| total_queries | bigint | Total number of queries |
| cache_hits | bigint | Number of cache hits |
| cache_misses | bigint | Number of cache misses |
| hit_rate | float4 | Hit rate percentage |
| total_cost_saved | float8 | Total money saved |
| avg_cost_per_hit | float8 | Average savings per hit |
| total_cost_if_no_cache | float8 | Cost without cache |

In the following example, the function returns cost savings for the
last 30 days:

```sql
SELECT * FROM semantic_cache.get_cost_savings();
```

In the following example, the function returns cost savings for the
last 7 days:

```sql
SELECT * FROM semantic_cache.get_cost_savings(7);
```

In the following example, the query formats the cost savings output
for display:

```sql
SELECT
    total_queries,
    cache_hits,
    ROUND(hit_rate, 1) || '%' as hit_rate,
    '$' || ROUND(total_cost_saved, 2) as saved,
    '$' || ROUND(total_cost_if_no_cache, 2) as would_have_cost
FROM semantic_cache.get_cost_savings(30);
```

## Views

The following sections describe the views available for monitoring
cache access patterns and cost savings.

### cache_access_summary

The `cache_access_summary` view provides hourly cache access
statistics with cost savings information.

In the following example, the query retrieves hourly statistics for
the last 24 hours:

```sql
SELECT * FROM semantic_cache.cache_access_summary
ORDER BY hour DESC
LIMIT 24;
```

The view includes:

- the hour timestamp.
- the total accesses in that hour.
- the number of hits and misses.
- the hit rate percentage.
- the total cost saved.

### cost_savings_daily

The `cost_savings_daily` view provides a daily breakdown of cost
savings and query statistics.

In the following example, the query retrieves daily cost savings for
the last 7 days:

```sql
SELECT * FROM semantic_cache.cost_savings_daily
ORDER BY date DESC
LIMIT 7;
```

The view includes:

- the date.
- the total queries for that day.
- the number of cache hits and misses.
- the hit rate percentage.
- the total cost saved.
- the average savings per hit.

### top_cached_queries

The `top_cached_queries` view ranks queries by total cost savings.

In the following example, the query retrieves the top ten queries with
the highest cost savings:

```sql
SELECT * FROM semantic_cache.top_cached_queries
LIMIT 10;
```

The view includes:

- the query hash identifier.
- the number of times served from cache.
- the average similarity score.
- the total cost saved by this query.
- the last access time.

## Integration Examples

The following sections provide integration examples for Python and
Node.js applications.

### Python with OpenAI

In the following example, the Python code integrates cache logging
with OpenAI API calls:

```python
import psycopg2
import openai
import hashlib

conn = psycopg2.connect("dbname=mydb")
client = openai.OpenAI(api_key="your-key")

def query_with_cache(query_text, embedding):
    cur = conn.cursor()
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()

    cur.execute("""
        SELECT * FROM semantic_cache.get_cached_result(%s, 0.95)
    """, (embedding,))
    result = cur.fetchone()

    if result and result[0]:
        cur.execute("""
            SELECT semantic_cache.log_cache_access(%s, true, %s, 0.008)
        """, (query_hash, result[2]))
        conn.commit()
        return result[1]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query_text}]
    )
    usage = response.usage
    cost = (usage.prompt_tokens / 1000) * 0.03 + \
           (usage.completion_tokens / 1000) * 0.06
    result_json = response.choices[0].message.content
    cur.execute("""
        SELECT semantic_cache.cache_query(%s, %s, %s::jsonb, 3600)
    """, (query_text, embedding, result_json))
    cur.execute("""
        SELECT semantic_cache.log_cache_access(%s, false, NULL, %s)
    """, (query_hash, cost))

    conn.commit()
    return result_json
```

### Node.js with Anthropic

In the following example, the Node.js code integrates cache logging
with Anthropic API calls:

```javascript
const { Pool } = require('pg');
const Anthropic = require('@anthropic-ai/sdk');
const crypto = require('crypto');

const pool = new Pool({ database: 'mydb' });
const anthropic = new Anthropic();

async function queryWithCache(queryText, embedding) {
    const client = await pool.connect();
    const queryHash = crypto.createHash('sha256')
        .update(queryText).digest('hex');

    try {
        const cache = await client.query(
            'SELECT * FROM semantic_cache.get_cached_result($1, 0.95)',
            [embedding]
        );

        if (cache.rows[0]?.found) {
            await client.query(
                'SELECT semantic_cache.log_cache_access($1, $2, $3, $4)',
                [queryHash, true, cache.rows[0].similarity_score, 0.008]
            );
            return cache.rows[0].result_data;
        }
        const message = await anthropic.messages.create({
            model: "claude-3-5-sonnet-20241022",
            max_tokens: 1024,
            messages: [{ role: "user", content: queryText }]
        });
        const cost = (message.usage.input_tokens / 1_000_000) * 3.00 +
                     (message.usage.output_tokens / 1_000_000) * 15.00;
        await client.query(
            'SELECT semantic_cache.cache_query($1, $2, $3, 3600)',
            [queryText, embedding, JSON.stringify(message.content)]
        );
        await client.query(
            'SELECT semantic_cache.log_cache_access($1, $2, $3, $4)',
            [queryHash, false, null, cost]
        );

        return message.content;
    } finally {
        client.release();
    }
}
```

## Cost Calculation

The following sections describe how to calculate costs for logging
cache access.

### Where Costs Come From

You must calculate the cost from your LLM API response and provide it
when calling the `log_cache_access` function.

In the following example, the Python code calculates the cost for an
OpenAI GPT-4 API call:

```python
usage = response['usage']
input_cost = (usage['prompt_tokens'] / 1000) * 0.03
output_cost = (usage['completion_tokens'] / 1000) * 0.06
total_cost = input_cost + output_cost
```

### Current Pricing

The following table shows current pricing for common LLM models as of
January 2026:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4 Turbo | $10.00 | $30.00 |
| GPT-3.5 Turbo | $0.50 | $1.50 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

## Monitoring Dashboard

The following sections describe how to create monitoring dashboards
for cache performance.

In the following example, the query retrieves key cache metrics for a
monitoring dashboard:

```sql
SELECT
    (SELECT COUNT(*) FILTER (WHERE cache_hit = true)
     FROM semantic_cache.cache_access_log
     WHERE access_time >= NOW() - INTERVAL '24 hours') as hits_24h,
    (SELECT ROUND(SUM(cost_saved)::numeric, 4)
     FROM semantic_cache.cache_access_log
     WHERE access_time >= NOW() - INTERVAL '24 hours') as saved_24h,
    (SELECT total_cost_saved
     FROM semantic_cache.cache_metadata
     WHERE id = 1) as saved_all_time,
    (SELECT COUNT(*) FROM semantic_cache.cache_entries) as entries;
```

## Maintenance

The following sections describe maintenance tasks for the cache access
log.

### Manual Cleanup

In the following example, the commands perform manual cleanup of old
log entries:

```sql
DELETE FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '30 days';

SELECT pg_size_pretty(
    pg_total_relation_size('semantic_cache.cache_access_log'));

VACUUM semantic_cache.cache_access_log;
```

### Automated Cleanup

You can use the pg_cron extension to schedule automated cleanup
tasks.

In the following example, the pg_cron extension schedules daily
cleanup at 2 AM:

```sql
CREATE EXTENSION pg_cron;
SELECT cron.schedule(
    'semantic-cache-log-cleanup',
    '0 2 * * *',
    $$DELETE FROM semantic_cache.cache_access_log
      WHERE access_time < NOW() - INTERVAL '30 days'$$
);
```

## Database Schema

The following sections describe the database schema for logging and
cost tracking.

### Tables

The `cache_metadata` table tracks overall cache statistics:

```sql
id                 SERIAL PRIMARY KEY
total_hits         BIGINT DEFAULT 0
total_misses       BIGINT DEFAULT 0
total_cost_saved   NUMERIC(12,6) DEFAULT 0.0
```

The `cache_access_log` table records individual cache access events:

```sql
id                 BIGSERIAL PRIMARY KEY
access_time        TIMESTAMPTZ DEFAULT NOW()
query_hash         TEXT
cache_hit          BOOLEAN NOT NULL
similarity_score   REAL
query_cost         NUMERIC(10,6)
cost_saved         NUMERIC(10,6)
```

The table includes the following indexes:

- the `idx_access_log_time` index on `access_time`.
- the `idx_access_log_hash` index on `query_hash`.

## Troubleshooting

The following sections address common troubleshooting scenarios for
logging and cost tracking.

### No data in reports

If reports show no data, use the following troubleshooting queries.

The following query checks if logging is being performed:

```sql
SELECT COUNT(*) FROM semantic_cache.cache_access_log;
```

The following query checks the date range of logs:

```sql
SELECT MIN(access_time), MAX(access_time)
FROM semantic_cache.cache_access_log;
```

The following query tries a longer time period:

```sql
SELECT * FROM semantic_cache.get_cost_savings(365);
```

### Costs showing as zero

Ensure you are passing actual costs to the `log_cache_access`
function.

In the following example, an incorrect call passes zero as the cost:

```sql
SELECT semantic_cache.log_cache_access('hash', true, 0.95, 0);
```

In the following example, the correct call passes the actual cost:

```sql
SELECT semantic_cache.log_cache_access('hash', true, 0.95, 0.008);
```

### Storage growing too large

If the cache access log table is growing too large, archive old logs
before deleting them.

In the following example, the commands archive and delete old log
entries:

```sql
CREATE TABLE semantic_cache.cache_access_log_archive AS
SELECT * FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '90 days';

DELETE FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '90 days';

VACUUM semantic_cache.cache_access_log;
```

## Performance

The logging system has the following performance characteristics:

- The overhead is approximately 1 to 2ms per log entry.
- The storage requirement is approximately 100 bytes per log entry.
- The system creates automatic indexes on `access_time` and
  `query_hash`.
- The recommendation is to archive logs older than 30 to 90 days.

