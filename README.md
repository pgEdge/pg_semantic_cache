# pg_semantic_cache

### Intelligent Query Result Caching for PostgreSQL

**Leverage vector embeddings to cache and retrieve query results based on semantic similarity**

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%20|%2015%20|%2016%20|%2017%20|%2018-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-PostgreSQL-blue.svg)](LICENSE)
[![pgvector](https://img.shields.io/badge/Requires-pgvector-orange.svg)](https://github.com/pgvector/pgvector)

[Quick Start](#quick-start) •
[Features](#key-features) •
[API Reference](#api-reference) •
[Examples](#integration-examples) •
[Performance](#performance)

</div>

---

## Overview

`pg_semantic_cache` enables **semantic query result caching** in PostgreSQL. Unlike traditional caching that requires exact query matches, this extension uses vector embeddings to find and retrieve cached results for semantically similar queries.

### Perfect For

- **AI/LLM Applications** - Cache expensive LLM responses for similar questions
- **RAG Pipelines** - Speed up retrieval-augmented generation workflows
- **Analytics Dashboards** - Reuse results for similar analytical queries
- **Chatbots** - Reduce latency by caching semantically similar conversations
- **Search Systems** - Handle query variations without re-execution

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ Query: "What was Q4 2024 revenue?"                          │
│ ↓ Generate embedding via OpenAI/etc                         │
│ ↓ Check semantic cache (similarity > 95%)                   │
│                                                              │
│ Similar cached query found:                                 │
│ "Show me revenue for last quarter" (similarity: 97%)        │
│ ↓ Return cached result (2ms instead of 500ms)               │
│ Cache HIT - 250x faster!                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

`pg_semantic_cache` provides a comprehensive set of capabilities designed for production use.

### Semantic Intelligence
- **Vector-based matching** using pgvector for similarity search
- **Configurable similarity thresholds** (default: 95%)
- **Cosine distance** calculations for accurate semantic matching
- Support for any embedding model (OpenAI, Cohere, custom, etc.)

### High Performance
- **Sub-5ms cache lookups** with optimized vector indexing
- **Efficient storage** with minimal overhead per entry
- **Fast eviction** mechanisms to maintain cache health
- **Index optimization** support for large-scale deployments (100k+ entries)

### Flexible Cache Management
- **Multiple eviction policies**: LRU, LFU, and TTL-based
- **Per-query TTL** or global defaults
- **Tag-based organization** for grouped invalidation
- **Pattern-based invalidation** using SQL LIKE patterns
- **Auto-eviction** with configurable policies

### Observability & Monitoring
- **Real-time statistics**: hit rate, total entries, cache size
- **Health metrics**: expired entries, memory usage, eviction counts
- **Performance tracking**: lookup times, similarity scores
- **Built-in views** for monitoring and analysis

### Production Ready
- **Comprehensive logging** with configurable levels
- **Crash-safe** error handling
- **ACID compliance** for cache operations
- **Multi-version support**: PostgreSQL 14 through 18+
- **Standard PGXS** build system for easy packaging

---

## Quick Start

### Installation

**Step 1: Install Dependencies**

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-16 postgresql-server-dev-16 postgresql-16-pgvector

# Rocky Linux/RHEL
sudo dnf install postgresql16 postgresql16-devel postgresql16-contrib

# macOS (with Homebrew)
brew install postgresql@16
# Install pgvector separately
```

**Step 2: Build & Install Extension**

```bash
git clone https://github.com/pgedge/pg_semantic_cache.git
cd pg_semantic_cache

make clean && make
sudo make install
```

**Step 3: Enable in PostgreSQL**

```sql
-- Connect to your database
psql -U postgres -d your_database

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Initialize the cache schema (run once per database)
SELECT semantic_cache.init_schema();

-- Verify installation
SELECT * FROM semantic_cache.cache_stats();
```

**You're ready to go!**

---

## Basic Usage

### 1. Cache a Query Result

```sql
SELECT semantic_cache.cache_query(
    query_text    := 'SELECT * FROM orders WHERE status = ''completed''',
    embedding     := '[0.1, 0.2, 0.3, ...]'::text,  -- From OpenAI, Cohere, etc.
    result_data   := '{"total": 150, "orders": [...]}'::jsonb,
    ttl_seconds   := 3600,                          -- 1 hour
    tags          := ARRAY['orders', 'analytics']   -- Optional tags
);
-- Returns: cache_id (bigint)
```

### 2. Retrieve Cached Result

```sql
SELECT * FROM semantic_cache.get_cached_result(
    embedding            := '[0.11, 0.19, 0.31, ...]'::text,  -- Similar query embedding
    similarity_threshold := 0.95,                              -- 95% similarity required
    max_age_seconds      := NULL                               -- Any age (optional)
);
-- Returns: (found boolean, result_data jsonb, similarity_score float4, age_seconds int)
```

**Example Result:**
```
 found |        result_data         | similarity_score | age_seconds
-------+----------------------------+------------------+-------------
 true  | {"total": 150, "orders"... | 0.973            | 245
```

### 3. Monitor Performance

```sql
-- Comprehensive statistics
SELECT * FROM semantic_cache.cache_stats();

-- Health overview (includes hit rate and more details)
SELECT * FROM semantic_cache.cache_health;

-- Recent cache activity
SELECT * FROM semantic_cache.recent_cache_activity LIMIT 10;
```

---

## API Reference

The extension provides a complete set of SQL functions for caching, eviction, monitoring, and configuration.

### Core Functions

#### `init_schema()`
Initialize the cache schema, creating all required tables, indexes, and views.

```sql
SELECT semantic_cache.init_schema();
```

#### `cache_query(query_text, embedding, result_data, ttl_seconds, tags)`
Store a query result with its embedding for future retrieval.

**Parameters:**
- `query_text` (text) - The original query text
- `embedding` (text) - Vector embedding as text: `'[0.1, 0.2, ...]'`
- `result_data` (jsonb) - The query result to cache
- `ttl_seconds` (int) - Time-to-live in seconds
- `tags` (text[]) - Optional tags for organization

**Returns:** `bigint` - Cache entry ID

#### `get_cached_result(embedding, similarity_threshold, max_age_seconds)`
Retrieve a cached result by semantic similarity.

**Parameters:**
- `embedding` (text) - Query embedding to search for
- `similarity_threshold` (float4) - Minimum similarity (0.0 to 1.0)
- `max_age_seconds` (int) - Maximum age in seconds (NULL = any age)

**Returns:** `record` - `(found boolean, result_data jsonb, similarity_score float4, age_seconds int)`


---

### Cache Eviction

Multiple eviction strategies are available to manage cache size and freshness.

#### `evict_expired()`
Remove all expired cache entries.

```sql
SELECT semantic_cache.evict_expired();  -- Returns count of evicted entries
```

#### `evict_lru(keep_count)`
Evict least recently used entries, keeping only the specified number of most recent entries.

```sql
SELECT semantic_cache.evict_lru(1000);  -- Keep only 1000 most recently used entries
```

#### `evict_lfu(keep_count)`
Evict least frequently used entries, keeping only the specified number of most frequently used entries.

```sql
SELECT semantic_cache.evict_lfu(1000);  -- Keep only 1000 most frequently used entries
```

#### `auto_evict()`
Automatically evict entries based on configured policy (LRU, LFU, or TTL).

```sql
SELECT semantic_cache.auto_evict();
```

#### `clear_cache()`
Remove **all** cache entries (use with caution).

```sql
SELECT semantic_cache.clear_cache();
```

---

### Statistics & Monitoring

Built-in functions and views provide real-time visibility into cache performance.

#### `cache_stats()`
Get comprehensive cache statistics.

```sql
SELECT * FROM semantic_cache.cache_stats();
```

**Returns:**
```
total_entries      | Total number of cached queries
total_hits         | Total number of cache hits
total_misses       | Total number of cache misses
hit_rate_percent   | Hit rate as a percentage
```

**Note:** For more detailed statistics including cache size, expired entries, and access patterns, use the `semantic_cache.cache_health` view.

---

### Configuration

All runtime settings can be configured through the cache configuration table.

Configuration settings are stored in the `semantic_cache.cache_config` table. You can view and modify them directly:

```sql
-- View all configuration
SELECT * FROM semantic_cache.cache_config ORDER BY key;

-- Update configuration (direct SQL)
INSERT INTO semantic_cache.cache_config (key, value)
VALUES ('max_cache_size_mb', '2000')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Get specific config value
SELECT value FROM semantic_cache.cache_config WHERE key = 'eviction_policy';
```

**Common Configuration Keys:**
| Key | Example Value | Description |
|-----|---------------|-------------|
| `max_cache_size_mb` | '1000' | Maximum cache size in megabytes |
| `default_ttl_seconds` | '3600' | Default TTL for cached entries |
| `eviction_policy` | 'lru' | Eviction policy: lru, lfu, or ttl |
| `similarity_threshold` | '0.95' | Default similarity threshold |

---

## Build & Development

The extension uses the standard PostgreSQL PGXS build system for compilation and installation.

### Build Commands

```bash
# Standard build
make clean && make
sudo make install

# Run tests
make installcheck

# Development build with debug symbols
make CFLAGS="-g -O0" clean all

# View build configuration
make info
```

### Multi-Version PostgreSQL Build

Build for multiple PostgreSQL versions simultaneously:

```bash
for PG in 14 15 16 17 18; do
    echo "Building for PostgreSQL $PG..."
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```

### Cross-Platform Support

Fully compatible with all PostgreSQL-supported platforms:

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Supported | Ubuntu, Debian, RHEL, Rocky, Fedora, etc. |
| macOS | Supported | Intel & Apple Silicon |
| Windows | Supported | Via MinGW or MSVC |
| BSD | Supported | FreeBSD, OpenBSD |

### Tested PostgreSQL Versions

| Version | Status | Notes |
|---------|--------|-------|
| PG 14 | Tested | Full support |
| PG 15 | Tested | Full support |
| PG 16 | Tested | Full support |
| PG 17 | Tested | Full support |
| PG 18 | Tested | Full support |
| Future versions | Expected | Standard PGXS compatibility |

---

## Performance

The extension is optimized for sub-millisecond cache lookups with minimal overhead.

### Runtime Metrics

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Cache lookup | **< 5ms** | With optimized vector index |
| Cache insert | **< 10ms** | Including embedding storage |
| Eviction (1000 entries) | **< 50ms** | Efficient batch operations |
| Statistics query | **< 1ms** | Materialized views |
| Similarity search | **2-3ms avg** | IVFFlat/HNSW indexed |

### Expected Hit Rates

| Workload Type | Typical Hit Rate |
|---------------|------------------|
| AI/LLM queries | 40-60% |
| Analytics dashboards | 60-80% |
| Search systems | 50-70% |
| Chatbot conversations | 45-65% |

### Memory Overhead

- **Per cache entry**: ~1-2KB (metadata + indexes)
- **Vector storage**: Depends on embedding dimension (1536D = ~6KB)
- **Total overhead**: Minimal for typical workloads

### Benchmarks

Run the included benchmark suite:

```bash
psql -U postgres -d your_database -f test/benchmark.sql
```

**Expected Results:**

```
Operation              | Count  | Total Time | Avg Time
-----------------------+--------+------------+----------
Insert entries         | 1,000  | ~500ms     | 0.5ms
Lookup (hits)          | 100    | ~200ms     | 2.0ms
Lookup (misses)        | 100    | ~150ms     | 1.5ms
Evict LRU              | 500    | ~25ms      | 0.05ms
```

---

## Production Deployment

For production environments, optimize PostgreSQL settings and set up automated maintenance.

### PostgreSQL Configuration

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

**HNSW Benefits:**
- Faster queries (1-2ms vs 3-5ms)
- Better recall at high similarity thresholds
- Scales linearly with cache size

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

## Integration Examples

### Python with OpenAI

Complete example integrating semantic cache with OpenAI embeddings:

```python
import psycopg2
import openai
import json
from typing import Optional, Dict, Any

class SemanticCache:
    """Semantic cache wrapper for PostgreSQL"""

    def __init__(self, conn_string: str, openai_api_key: str):
        self.conn = psycopg2.connect(conn_string)
        self.client = openai.OpenAI(api_key=openai_api_key)

    def _get_embedding(self, text: str) -> str:
        """Generate embedding using OpenAI"""
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        return f"[{','.join(map(str, embedding))}]"

    def cache(self, query: str, result: Dict[Any, Any],
              ttl: int = 3600, tags: Optional[list] = None) -> int:
        """Cache a query result"""
        embedding = self._get_embedding(query)

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT semantic_cache.cache_query(
                    %s::text, %s::text, %s::jsonb, %s::int, %s::text[]
                )
            """, (query, embedding, json.dumps(result), ttl, tags))
            cache_id = cur.fetchone()[0]
            self.conn.commit()
            return cache_id

    def get(self, query: str, similarity: float = 0.95,
            max_age: Optional[int] = None) -> Optional[Dict[Any, Any]]:
        """Retrieve from cache"""
        embedding = self._get_embedding(query)

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT found, result_data, similarity_score, age_seconds
                FROM semantic_cache.get_cached_result(
                    %s::text, %s::float4, %s::int
                )
            """, (embedding, similarity, max_age))

            result = cur.fetchone()
            if result and result[0]:  # Cache hit
                print(f"Cache HIT (similarity: {result[2]:.3f}, age: {result[3]}s)")
                return json.loads(result[1])
            else:
                print("Cache MISS")
                return None

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM semantic_cache.cache_stats()")
            columns = [desc[0] for desc in cur.description]
            values = cur.fetchone()
            return dict(zip(columns, values))

# Usage example
cache = SemanticCache(
    conn_string="dbname=mydb user=postgres",
    openai_api_key="sk-..."
)

# Try to get from cache, compute if miss
def get_revenue_data(query: str) -> Dict:
    result = cache.get(query, similarity=0.95)

    if result:
        return result  # Cache hit!

    # Cache miss - compute the result
    result = expensive_database_query()  # Your expensive query here
    cache.cache(query, result, ttl=3600, tags=['revenue', 'analytics'])
    return result

# Example queries
data1 = get_revenue_data("What was Q4 2024 revenue?")
data2 = get_revenue_data("Show me revenue for last quarter")  # Will hit cache!
data3 = get_revenue_data("Q4 sales figures?")  # Will also hit cache!

# View statistics
print(cache.stats())
```

### Node.js with OpenAI

```javascript
const { Client } = require('pg');
const OpenAI = require('openai');

class SemanticCache {
    constructor(pgConfig, openaiApiKey) {
        this.client = new Client(pgConfig);
        this.openai = new OpenAI({ apiKey: openaiApiKey });
        this.client.connect();
    }

    async getEmbedding(text) {
        const response = await this.openai.embeddings.create({
            model: 'text-embedding-ada-002',
            input: text
        });
        const embedding = response.data[0].embedding;
        return `[${embedding.join(',')}]`;
    }

    async cache(query, result, ttl = 3600, tags = null) {
        const embedding = await this.getEmbedding(query);
        const res = await this.client.query(
            `SELECT semantic_cache.cache_query($1::text, $2::text, $3::jsonb, $4::int, $5::text[])`,
            [query, embedding, JSON.stringify(result), ttl, tags]
        );
        return res.rows[0].cache_query;
    }

    async get(query, similarity = 0.95, maxAge = null) {
        const embedding = await this.getEmbedding(query);
        const res = await this.client.query(
            `SELECT * FROM semantic_cache.get_cached_result($1::text, $2::float4, $3::int)`,
            [embedding, similarity, maxAge]
        );

        const { found, result_data, similarity_score, age_seconds } = res.rows[0];

        if (found) {
            console.log(`Cache HIT (similarity: ${similarity_score.toFixed(3)}, age: ${age_seconds}s)`);
            return JSON.parse(result_data);
        } else {
            console.log('Cache MISS');
            return null;
        }
    }

    async stats() {
        const res = await this.client.query('SELECT * FROM semantic_cache.cache_stats()');
        return res.rows[0];
    }
}

// Usage
const cache = new SemanticCache(
    { host: 'localhost', database: 'mydb', user: 'postgres' },
    'sk-...'
);

async function getRevenueData(query) {
    const cached = await cache.get(query);
    if (cached) return cached;

    const result = await expensiveDatabaseQuery();
    await cache.cache(query, result, 3600, ['revenue', 'analytics']);
    return result;
}
```

### More Examples

For additional integration patterns and use cases, see:
- `examples/usage_examples.sql` - Comprehensive SQL examples
- `test/benchmark.sql` - Performance testing examples

---

## Contributing

Contributions are welcome! This extension is built with standard PostgreSQL C APIs.

**Development setup:**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make installcheck`
5. Submit a pull request

**Code guidelines:**
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure compatibility with PostgreSQL 14-18

---

## License

This project is licensed under the **PostgreSQL License**.

---

## Support & Resources

- **GitHub Issues**: Report bugs and request features
- **Example Code**: Check `examples/` directory for usage patterns
- **Test Suite**: See `test/` directory for comprehensive examples
