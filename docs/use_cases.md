# Use Cases

This document provides practical examples and integration patterns for the
pg_semantic_cache extension in real-world applications.

## LLM and AI Applications

The following sections demonstrate how to use the pg_semantic_cache extension
to optimize costs and performance in LLM and AI-powered applications.

### RAG (Retrieval Augmented Generation) Caching

The RAG caching pattern addresses the challenge of expensive LLM API
calls by caching responses based on semantic similarity of user
questions.

LLM API calls typically cost between $0.02 and $0.05 per request, and
users often ask similar questions using different wording. The
pg_semantic_cache extension solves this problem by caching LLM
responses with semantic matching.

In the following example, the `SemanticLLMCache` class uses the
OpenAI API to generate embeddings and cache LLM responses based on
semantic similarity.

```python
import openai
import psycopg2
import json

class SemanticLLMCache:
    def __init__(self, db_conn_string):
        self.conn = psycopg2.connect(db_conn_string)
        self.openai_client = openai.OpenAI()

    def get_embedding(self, text):
        """Generate embedding for text"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    def ask_llm_cached(self, question, context="", similarity=0.93):
        """Ask LLM with caching"""
        # Generate embedding for question
        embedding = self.get_embedding(question)
        embedding_str = str(embedding)

        # Try cache first
        cur = self.conn.cursor()
        cur.execute("""
            SELECT found, result_data, similarity_score, age_seconds
            FROM semantic_cache.get_cached_result(%s, %s)
        """, (embedding_str, similarity))

        result = cur.fetchone()
        if result:  # Cache hit
            print(f"✓ Cache HIT (similarity: {result[2]:.4f}, "
                  f"age: {result[3]}s)")
            return json.loads(result[1])

        # Cache miss - call actual LLM
        print("✗ Cache MISS - calling OpenAI API")
        llm_response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ]
        )

        answer = llm_response.choices[0].message.content
        tokens = llm_response.usage.total_tokens

        # Cache the response
        result_data = json.dumps({
            "answer": answer,
            "tokens": tokens,
            "model": "gpt-4"
        })

        cur.execute("""
            SELECT semantic_cache.cache_query(
                %s, %s, %s::jsonb, 7200, ARRAY['llm', 'rag']
            )
        """, (question, embedding_str, result_data))
        self.conn.commit()

        return {"answer": answer, "tokens": tokens}

# Usage
cache = SemanticLLMCache("dbname=mydb user=postgres")

# These similar questions will hit the cache
cache.ask_llm_cached("What was our Q4 revenue?")
cache.ask_llm_cached("Show me Q4 revenue")     # Cache hit!
cache.ask_llm_cached("Q4 revenue please")      # Cache hit!
```

An organization processing 10,000 daily queries with an 80% cache hit
rate can save approximately $140 per day or $51,100 per year using this
approach.

### Chatbot Response Caching

The chatbot response caching pattern optimizes conversational AI
applications by storing and reusing responses for semantically
similar user messages.

In the following example, the `ChatbotCache` class uses TypeScript to
implement a caching layer for chatbot responses with configurable
similarity thresholds.

```typescript
import { OpenAI } from 'openai';
import { Pool } from 'pg';

interface CachedResponse {
  answer: string;
  cached: boolean;
  similarity?: number;
}

class ChatbotCache {
  private openai: OpenAI;
  private pool: Pool;

  constructor(dbConfig: any) {
    this.openai = new OpenAI();
    this.pool = new Pool(dbConfig);
  }

  async getCachedResponse(
    userMessage: string,
    context: string[]
  ): Promise<CachedResponse> {
    // Generate embedding
    const embeddingResp = await this.openai.embeddings.create({
      model: 'text-embedding-ada-002',
      input: userMessage,
    });
    const embedding = embeddingResp.data[0].embedding;
    const embeddingStr = `[${embedding.join(',')}]`;

    // Check cache
    const cacheResult = await this.pool.query(
      `SELECT * FROM semantic_cache.get_cached_result($1, 0.92)`,
      [embeddingStr]
    );

    if (cacheResult.rows.length > 0) {
      return {
        answer: cacheResult.rows[0].result_data.answer,
        cached: true,
        similarity: cacheResult.rows[0].similarity_score,
      };
    }

    // Call LLM
    const completion = await this.openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: context.join('\n') },
        { role: 'user', content: userMessage },
      ],
    });

    const answer = completion.choices[0].message.content!;

    // Cache response
    await this.pool.query(
      `SELECT semantic_cache.cache_query(
         $1, $2, $3::jsonb, 3600, ARRAY['chatbot'])`,
      [userMessage, embeddingStr, JSON.stringify({ answer })]
    );

    return { answer, cached: false };
  }
}
```

## Analytics and Reporting

This section demonstrates how to use the pg_semantic_cache extension
to improve performance of analytical queries and reporting workloads.

### Dashboard Query Caching

The dashboard query caching pattern reduces latency for expensive
analytical queries that power business intelligence dashboards and
reporting tools.

In the following example, the `app.get_sales_analytics` function
uses a deterministic embedding to cache analytics results for a
configurable TTL period.

```sql
-- Application caching wrapper for analytics
CREATE OR REPLACE FUNCTION app.get_sales_analytics(
    query_text TEXT,
    params JSONB
) RETURNS JSONB AS $$
DECLARE
    query_embedding TEXT;
    cached_result RECORD;
    actual_result JSONB;
    computation_time INTERVAL;
    start_time TIMESTAMPTZ;
BEGIN
    -- Generate deterministic embedding from query + params
    -- (In production, use actual embedding service)
    query_embedding := (
        SELECT array_agg(
            (hashtext((query_text || params::text)::text) + i)::float
            / 2147483647
        )::text
        FROM generate_series(1, 1536) i
    );

    -- Try cache
    SELECT * INTO cached_result
    FROM semantic_cache.get_cached_result(
        query_embedding,
        0.95,
        1800  -- Max 30 minutes old
    );

    IF cached_result.found IS NOT NULL THEN
        -- Cache hit
        RAISE NOTICE 'Cache HIT - saved query execution';
        RETURN cached_result.result_data;
    END IF;

    -- Cache miss - execute expensive query
    RAISE NOTICE 'Cache MISS - executing analytics query';
    start_time := clock_timestamp();

    -- Example: Complex analytics query
    SELECT jsonb_build_object(
        'total_revenue', SUM(amount),
        'order_count', COUNT(*),
        'avg_order_value', AVG(amount),
        'period', params->>'period'
    ) INTO actual_result
    FROM orders
    WHERE created_at >= (params->>'start_date')::timestamptz
      AND created_at <= (params->>'end_date')::timestamptz
      AND status = 'completed';

    computation_time := clock_timestamp() - start_time;
    RAISE NOTICE 'Query executed in %', computation_time;

    -- Cache result (longer TTL for analytics)
    PERFORM semantic_cache.cache_query(
        query_text,
        query_embedding,
        actual_result,
        7200,  -- 2 hours
        ARRAY['analytics', 'dashboard']
    );

    RETURN actual_result;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT app.get_sales_analytics(
    'Total sales and order metrics',
    '{"period": "Q4", "start_date": "2024-10-01",
      "end_date": "2024-12-31"}'::jsonb
);
```

### Time-Series Report Caching

The time-series report caching pattern optimizes recurring reports by
adjusting cache TTL based on the temporal granularity of the data
being reported.

In the following example, the `app.cached_time_series_report`
function uses different TTL values for daily, weekly, and monthly
reports.

```sql
-- Cache daily/weekly/monthly reports
CREATE OR REPLACE FUNCTION app.cached_time_series_report(
    report_type TEXT,   -- 'daily', 'weekly', 'monthly'
    metric_name TEXT
) RETURNS TABLE(period DATE, value NUMERIC) AS $$
DECLARE
    query_emb TEXT;
    cached RECORD;
    ttl_seconds INTEGER;
BEGIN
    -- Generate embedding (simplified)
    query_emb := (
        SELECT array_agg(random()::float4)::text
        FROM generate_series(1, 1536)
    );

    -- Adjust TTL based on granularity
    ttl_seconds := CASE report_type
        WHEN 'daily' THEN 3600      -- 1 hour
        WHEN 'weekly' THEN 14400    -- 4 hours
        WHEN 'monthly' THEN 86400   -- 24 hours
    END;

    -- Try cache
    SELECT * INTO cached
    FROM semantic_cache.get_cached_result(query_emb, 0.95);

    IF cached.found IS NOT NULL THEN
        -- Return cached data as table
        RETURN QUERY
        SELECT
            (item->>'period')::DATE,
            (item->>'value')::NUMERIC
        FROM jsonb_array_elements(cached.result_data->'data') item;
        RETURN;
    END IF;

    -- Execute and cache (simplified example)
    PERFORM semantic_cache.cache_query(
        format('Report: %s - %s', report_type, metric_name),
        query_emb,
        '{"data": []}'::jsonb,   -- Your actual query results
        ttl_seconds,
        ARRAY['reports', report_type]
    );

    RETURN QUERY SELECT NULL::DATE, NULL::NUMERIC WHERE FALSE;
END;
$$ LANGUAGE plpgsql;
```

## External API Results

This section demonstrates how to use the pg_semantic_cache extension
to reduce costs and latency when integrating with third-party
external APIs.

### Third-Party API Response Caching

The external API caching pattern stores responses from expensive
third-party APIs such as weather services, geocoding providers, and
stock price feeds.

In the following example, the `APICache` class uses the
sentence-transformers library to generate embeddings and cache API
responses with semantic matching.

```python
import requests
import psycopg2
from sentence_transformers import SentenceTransformer

class APICache:
    def __init__(self, db_conn_string):
        self.conn = psycopg2.connect(db_conn_string)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

    def fetch_with_cache(self, query, api_call_fn, ttl=3600):
        """
        Fetch from API with semantic caching

        Args:
            query: Natural language query
                   (e.g., "weather in San Francisco")
            api_call_fn: Function to call API
            ttl: Cache TTL in seconds
        """
        # Generate embedding
        embedding = self.encoder.encode(query)
        embedding_str = str(embedding.tolist())

        # Check cache
        cur = self.conn.cursor()
        cur.execute("""
            SELECT found, result_data
            FROM semantic_cache.get_cached_result(%s, 0.90, %s)
        """, (embedding_str, ttl))

        result = cur.fetchone()
        if result:
            print(f"✓ Using cached API response")
            return result[1]

        # Call actual API
        print(f"✗ Calling external API")
        api_response = api_call_fn()

        # Cache response
        import json
        cur.execute("""
            SELECT semantic_cache.cache_query(
                %s, %s, %s::jsonb, %s,
                ARRAY['api', 'external']
            )
        """, (query, embedding_str, json.dumps(api_response), ttl))
        self.conn.commit()

        return api_response
```

The following examples demonstrate how to use the `APICache` class
with different external APIs using appropriate TTL values for each
use case.

```python
# Weather API
def get_weather(city):
    cache = APICache("dbname=mydb")
    return cache.fetch_with_cache(
        f"weather in {city}",
        lambda: requests.get(
            f"https://api.weather.com/{city}").json(),
        ttl=1800   # 30 minutes
    )

# Geocoding API
def geocode(address):
    cache = APICache("dbname=mydb")
    return cache.fetch_with_cache(
        f"geocode {address}",
        lambda: requests.get(
            f"https://api.geocode.com?q={address}").json(),
        ttl=86400  # 24 hours (addresses don't change)
    )

# Stock prices
def get_stock_price(symbol):
    cache = APICache("dbname=mydb")
    return cache.fetch_with_cache(
        f"stock price {symbol}",
        lambda: requests.get(
            f"https://api.stocks.com/{symbol}").json(),
        ttl=60     # 1 minute (real-time data)
    )
```

## Database Query Optimization

This section demonstrates how to use the pg_semantic_cache extension
to optimize expensive database queries and reduce computational
overhead.

### Expensive Join Caching

The expensive join caching pattern stores results from complex
multi-table joins to avoid repeated execution of resource-intensive
database operations.

In the following example, the `app.get_customer_summary` function
caches the results of a complex customer data aggregation query with
multiple joins.

```sql
-- Wrap expensive queries with semantic caching
CREATE OR REPLACE FUNCTION app.get_customer_summary(
    customer_identifier TEXT   -- email, name, or ID
) RETURNS JSONB AS $$
DECLARE
    query_emb TEXT;
    cached RECORD;
    result JSONB;
BEGIN
    -- Simple embedding generation (replace with actual service)
    query_emb := (
        SELECT array_agg(
            (hashtext(customer_identifier || i::text)::float
             / 2147483647)::float4
        )::text
        FROM generate_series(1, 1536) i
    );

    -- Check cache
    SELECT * INTO cached
    FROM semantic_cache.get_cached_result(
        query_emb, 0.98, 300
    );

    IF cached.found IS NOT NULL THEN
        RETURN cached.result_data;
    END IF;

    -- Execute expensive query
    WITH customer_data AS (
        SELECT
            c.id,
            c.name,
            c.email,
            COUNT(DISTINCT o.id) as total_orders,
            SUM(o.amount) as lifetime_value,
            AVG(o.amount) as avg_order_value,
            MAX(o.created_at) as last_order_date
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE c.email ILIKE '%' || customer_identifier || '%'
           OR c.name ILIKE '%' || customer_identifier || '%'
           OR c.id::text = customer_identifier
        GROUP BY c.id, c.name, c.email
    )
    SELECT jsonb_build_object(
        'customer', row_to_json(cd.*)
    ) INTO result
    FROM customer_data cd;

    -- Cache for 5 minutes
    PERFORM semantic_cache.cache_query(
        'Customer summary: ' || customer_identifier,
        query_emb,
        result,
        300,
        ARRAY['customer', 'summary']
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Usage - these similar queries hit cache:
SELECT app.get_customer_summary('[email protected]');
SELECT app.get_customer_summary('john@example.com');
    -- Exact match
SELECT app.get_customer_summary('John Doe');
    -- By name
SELECT app.get_customer_summary('john');
    -- Partial match
```

## Scheduled Maintenance

This section demonstrates how to implement automated maintenance
routines for the pg_semantic_cache extension to ensure optimal
performance and storage use.

### Automatic Cache Cleanup

The automatic cache cleanup pattern uses scheduled maintenance
functions to evict expired entries and optimize cache storage on a
regular basis.

In the following example, the `semantic_cache.scheduled_maintenance`
function performs multiple maintenance operations and returns timing
information.

```sql
-- Create maintenance function
CREATE OR REPLACE FUNCTION semantic_cache.scheduled_maintenance()
RETURNS TABLE(
    operation TEXT,
    affected_rows BIGINT,
    duration INTERVAL
) AS $$
DECLARE
    start_time TIMESTAMPTZ;
    evicted BIGINT;
BEGIN
    -- 1. Evict expired entries
    start_time := clock_timestamp();
    evicted := semantic_cache.evict_expired();
    RETURN QUERY SELECT
        'evict_expired'::TEXT,
        evicted,
        clock_timestamp() - start_time;

    -- 2. Auto-evict based on policy
    start_time := clock_timestamp();
    evicted := semantic_cache.auto_evict();
    RETURN QUERY SELECT
        'auto_evict'::TEXT,
        evicted,
        clock_timestamp() - start_time;

    -- 3. Analyze tables
    start_time := clock_timestamp();
    EXECUTE 'ANALYZE semantic_cache.cache_entries';
    EXECUTE 'ANALYZE semantic_cache.cache_metadata';
    RETURN QUERY SELECT
        'analyze_tables'::TEXT,
        0::BIGINT,
        clock_timestamp() - start_time;
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron (if available)
-- Run every hour
SELECT cron.schedule(
    'cache-maintenance',
    '0 * * * *',
    'SELECT semantic_cache.scheduled_maintenance()'
);

-- Or run manually
SELECT * FROM semantic_cache.scheduled_maintenance();
```

### Cache Warming

The cache warming pattern pre-populates the cache with common queries
to improve application performance during startup or after cache
invalidation.

In the following example, the `app.warm_cache` function pre-caches
frequently accessed dashboard queries to reduce initial page load
times.

```sql
-- Warm cache with popular queries
CREATE OR REPLACE FUNCTION app.warm_cache()
RETURNS INTEGER AS $$
DECLARE
    warmed_count INTEGER := 0;
BEGIN
    -- Example: Pre-cache common dashboard queries
    PERFORM semantic_cache.cache_query(
        'Total sales this month',
        (SELECT array_agg(random()::float4)::text
         FROM generate_series(1, 1536)),
        (SELECT jsonb_build_object('total', SUM(amount))
         FROM orders
         WHERE created_at >= DATE_TRUNC('month', NOW())),
        3600,
        ARRAY['dashboard', 'warmed']
    );
    warmed_count := warmed_count + 1;

    -- Add more common queries...

    RETURN warmed_count;
END;
$$ LANGUAGE plpgsql;

-- Run on application startup or schedule daily
SELECT app.warm_cache();
```

## Multi-Language Support

This section demonstrates how to use the pg_semantic_cache extension
to support caching across multiple languages using multilingual
embedding models.

### Caching Across Languages

The multilingual caching pattern enables cache hits across different
languages by using multilingual embedding models that map
semantically similar queries.

In the following example, the `MultilingualCache` class uses the
multilingual mpnet model to cache queries across English, Spanish,
French, and Portuguese.

```python
from sentence_transformers import SentenceTransformer
import psycopg2

class MultilingualCache:
    def __init__(self, db_conn_string):
        self.conn = psycopg2.connect(db_conn_string)
        # Use multilingual model
        self.encoder = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2'
        )

    def cached_query(self, query_text, language):
        """Cache works across languages!"""
        embedding = self.encoder.encode(query_text)
        embedding_str = str(embedding.tolist())

        # Check cache (works for all languages)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT *
            FROM semantic_cache.get_cached_result(%s, 0.90)
        """, (embedding_str,))

        result = cur.fetchone()
        if result:
            return result[1]

        # Execute query and cache
        # ... your query logic ...

# These queries in different languages can hit the same cache
# entry!
cache = MultilingualCache("dbname=mydb")

cache.cached_query("What is the total revenue?", "en")
cache.cached_query("¿Cuál es el ingreso total?", "es")
    # Cache hit!
cache.cached_query("Quel est le revenu total?", "fr")
    # Cache hit!
cache.cached_query("Qual é a receita total?", "pt")
    # Cache hit!
```

## Next Steps

The following resources provide additional information about the
pg_semantic_cache extension:

- The [Functions Reference](functions/index.md) document describes all
  available functions.
- The [Monitoring](monitoring.md) document explains how to track cache
  performance.
- The [Configuration](configuration.md) document provides optimization
  guidance for your use case.
- The [FAQ](FAQ.md) document answers common questions and provides
  solutions.
