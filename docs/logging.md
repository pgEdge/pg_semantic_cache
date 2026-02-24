# Logging & Cost Tracking

Track cache hits/misses and calculate cost savings from avoided LLM API calls.

## Quick Start

```sql
-- Log a cache miss (cost incurred)
SELECT semantic_cache.log_cache_access('query_hash', false, NULL, 0.006);

-- Log a cache hit (cost saved)
SELECT semantic_cache.log_cache_access('query_hash', true, 0.95, 0.006);

-- Get cost savings for last 7 days
SELECT * FROM semantic_cache.get_cost_savings(7);

-- View daily summary
SELECT * FROM semantic_cache.cost_savings_daily ORDER BY date DESC LIMIT 7;
```

---

## Functions

### `log_cache_access()`

Record a cache access event with cost information.

```sql
SELECT semantic_cache.log_cache_access(
    query_hash text,           -- Unique identifier for the query (e.g., SHA-256 hash)
    cache_hit boolean,         -- true = hit, false = miss
    similarity_score float4,   -- Similarity score (0-1), NULL for misses
    query_cost numeric         -- Cost of the query in dollars (e.g., 0.006)
);
```

**Examples:**
```sql
-- Log a cache miss (had to call LLM)
SELECT semantic_cache.log_cache_access('abc123...', false, NULL, 0.008);

-- Log a cache hit (saved LLM call)
SELECT semantic_cache.log_cache_access('def456...', true, 0.97, 0.008);
```

### `get_cost_savings()`

Get cost savings report for a time period.

```sql
SELECT * FROM semantic_cache.get_cost_savings(
    days integer DEFAULT 30    -- Number of days to analyze
);
```

**Returns:**

| Column | Type | Description |
|--------|------|-------------|
| total_queries | bigint | Total number of queries |
| cache_hits | bigint | Number of cache hits |
| cache_misses | bigint | Number of cache misses |
| hit_rate | float4 | Hit rate percentage (0-100) |
| total_cost_saved | float8 | Total money saved |
| avg_cost_per_hit | float8 | Average savings per hit |
| total_cost_if_no_cache | float8 | What it would have cost without cache |

**Examples:**
```sql
-- Last 30 days (default)
SELECT * FROM semantic_cache.get_cost_savings();

-- Last 7 days
SELECT * FROM semantic_cache.get_cost_savings(7);

-- Formatted output
SELECT
    total_queries,
    cache_hits,
    ROUND(hit_rate, 1) || '%' as hit_rate,
    '$' || ROUND(total_cost_saved, 2) as saved,
    '$' || ROUND(total_cost_if_no_cache, 2) as would_have_cost
FROM semantic_cache.get_cost_savings(30);
```

---

## Views

### `cache_access_summary`

Hourly cache access statistics with cost savings.

```sql
SELECT * FROM semantic_cache.cache_access_summary
ORDER BY hour DESC
LIMIT 24;
```

**Columns:**
- `hour` - Hour timestamp
- `total_accesses` - Total accesses in that hour
- `hits` - Number of hits
- `misses` - Number of misses
- `hit_rate_pct` - Hit rate percentage
- `cost_saved` - Total cost saved

### `cost_savings_daily`

Daily cost breakdown and savings analysis.

```sql
SELECT * FROM semantic_cache.cost_savings_daily
ORDER BY date DESC
LIMIT 7;
```

**Columns:**
- `date` - Date
- `total_queries` - Total queries that day
- `cache_hits` - Number of hits
- `cache_misses` - Number of misses
- `hit_rate_pct` - Hit rate percentage
- `total_cost_saved` - Total cost saved
- `avg_cost_per_hit` - Average savings per hit

### `top_cached_queries`

Top queries ranked by total cost savings.

```sql
SELECT * FROM semantic_cache.top_cached_queries
LIMIT 10;
```

**Columns:**
- `query_hash` - Query identifier
- `hit_count` - Number of times served from cache
- `avg_similarity` - Average similarity score
- `total_cost_saved` - Total cost saved by this query
- `last_access` - Last access time

---

## Integration Examples

### Python with OpenAI

```python
import psycopg2
import openai
import hashlib

conn = psycopg2.connect("dbname=mydb")
client = openai.OpenAI(api_key="your-key")

def query_with_cache(query_text, embedding):
    cur = conn.cursor()
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()

    # Check cache
    cur.execute("""
        SELECT * FROM semantic_cache.get_cached_result(%s, 0.95)
    """, (embedding,))
    result = cur.fetchone()

    if result and result[0]:  # Cache HIT
        cur.execute("""
            SELECT semantic_cache.log_cache_access(%s, true, %s, 0.008)
        """, (query_hash, result[2]))
        conn.commit()
        return result[1]

    # Cache MISS - call API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query_text}]
    )

    # Calculate cost
    usage = response.usage
    cost = (usage.prompt_tokens / 1000) * 0.03 + \
           (usage.completion_tokens / 1000) * 0.06

    # Cache result
    result_json = response.choices[0].message.content
    cur.execute("""
        SELECT semantic_cache.cache_query(%s, %s, %s::jsonb, 3600)
    """, (query_text, embedding, result_json))

    # Log miss
    cur.execute("""
        SELECT semantic_cache.log_cache_access(%s, false, NULL, %s)
    """, (query_hash, cost))

    conn.commit()
    return result_json
```

### Node.js with Anthropic

```javascript
const { Pool } = require('pg');
const Anthropic = require('@anthropic-ai/sdk');
const crypto = require('crypto');

const pool = new Pool({ database: 'mydb' });
const anthropic = new Anthropic();

async function queryWithCache(queryText, embedding) {
    const client = await pool.connect();
    const queryHash = crypto.createHash('sha256').update(queryText).digest('hex');

    try {
        // Check cache
        const cache = await client.query(
            'SELECT * FROM semantic_cache.get_cached_result($1, 0.95)',
            [embedding]
        );

        if (cache.rows[0]?.found) {
            // Cache HIT
            await client.query(
                'SELECT semantic_cache.log_cache_access($1, $2, $3, $4)',
                [queryHash, true, cache.rows[0].similarity_score, 0.008]
            );
            return cache.rows[0].result_data;
        }

        // Cache MISS - call API
        const message = await anthropic.messages.create({
            model: "claude-3-5-sonnet-20241022",
            max_tokens: 1024,
            messages: [{ role: "user", content: queryText }]
        });

        // Calculate cost
        const cost = (message.usage.input_tokens / 1_000_000) * 3.00 +
                     (message.usage.output_tokens / 1_000_000) * 15.00;

        // Cache result
        await client.query(
            'SELECT semantic_cache.cache_query($1, $2, $3, 3600)',
            [queryText, embedding, JSON.stringify(message.content)]
        );

        // Log miss
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

---

## Cost Calculation

### Where Costs Come From

You provide the cost when calling `log_cache_access()`. Calculate it from your LLM API response:

```python
# OpenAI GPT-4 example
usage = response['usage']
input_cost = (usage['prompt_tokens'] / 1000) * 0.03   # $0.03/1K tokens
output_cost = (usage['completion_tokens'] / 1000) * 0.06  # $0.06/1K tokens
total_cost = input_cost + output_cost
```

### Current Pricing (Jan 2026)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-4 Turbo | $10.00 | $30.00 |
| GPT-3.5 Turbo | $0.50 | $1.50 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

---

## Monitoring Dashboard

```sql
SELECT
    -- Last 24 hours
    (SELECT COUNT(*) FILTER (WHERE cache_hit = true)
     FROM semantic_cache.cache_access_log
     WHERE access_time >= NOW() - INTERVAL '24 hours') as hits_24h,

    (SELECT ROUND(SUM(cost_saved)::numeric, 4)
     FROM semantic_cache.cache_access_log
     WHERE access_time >= NOW() - INTERVAL '24 hours') as saved_24h,

    -- All time
    (SELECT total_cost_saved
     FROM semantic_cache.cache_metadata
     WHERE id = 1) as saved_all_time,

    -- Current cache size
    (SELECT COUNT(*) FROM semantic_cache.cache_entries) as entries;
```

---

## Maintenance

### Manual Cleanup

```sql
-- Delete logs older than 30 days
DELETE FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '30 days';

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('semantic_cache.cache_access_log'));

-- Reclaim space
VACUUM semantic_cache.cache_access_log;
```

### Automated Cleanup (pg_cron)

```sql
-- Install pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule daily cleanup at 2 AM
SELECT cron.schedule(
    'semantic-cache-log-cleanup',
    '0 2 * * *',
    $$DELETE FROM semantic_cache.cache_access_log
      WHERE access_time < NOW() - INTERVAL '30 days'$$
);
```

---

## Database Schema

### Tables

**cache_metadata:**
```sql
id                 SERIAL PRIMARY KEY
total_hits         BIGINT DEFAULT 0
total_misses       BIGINT DEFAULT 0
total_cost_saved   NUMERIC(12,6) DEFAULT 0.0
```

**cache_access_log:**
```sql
id                 BIGSERIAL PRIMARY KEY
access_time        TIMESTAMPTZ DEFAULT NOW()
query_hash         TEXT
cache_hit          BOOLEAN NOT NULL
similarity_score   REAL
query_cost         NUMERIC(10,6)
cost_saved         NUMERIC(10,6)
```

Indexes:
- `idx_access_log_time` on `access_time`
- `idx_access_log_hash` on `query_hash`

---

## Troubleshooting

### No data in reports

```sql
-- Check if logging is happening
SELECT COUNT(*) FROM semantic_cache.cache_access_log;

-- Check date range of logs
SELECT MIN(access_time), MAX(access_time)
FROM semantic_cache.cache_access_log;

-- Try longer time period
SELECT * FROM semantic_cache.get_cost_savings(365);
```

### Costs showing as $0

Ensure you're passing actual costs to `log_cache_access()`:

```sql
-- Wrong: passing 0
SELECT semantic_cache.log_cache_access('hash', true, 0.95, 0);

-- Correct: passing actual cost
SELECT semantic_cache.log_cache_access('hash', true, 0.95, 0.008);
```

### Storage growing too large

```sql
-- Archive old logs before deleting
CREATE TABLE semantic_cache.cache_access_log_archive AS
SELECT * FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '90 days';

DELETE FROM semantic_cache.cache_access_log
WHERE access_time < NOW() - INTERVAL '90 days';

VACUUM semantic_cache.cache_access_log;
```

---

## Performance

- **Overhead:** ~1-2ms per log entry
- **Storage:** ~100 bytes per log entry
- **Indexes:** Automatic on `access_time` and `query_hash`
- **Recommendation:** Archive logs older than 30-90 days

---

For more information, see the main [README](https://github.com/pgEdge/pg_semantic_cache#readme) and [CHANGELOG](https://github.com/pgEdge/pg_semantic_cache/blob/main/CHANGELOG.md).
