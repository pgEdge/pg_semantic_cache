# pg_semantic_cache

pg_semantic_cache allows you to leverage vector embeddings to cache and
retrieve query results based on semantic similarity.

## Table of Contents

- [pg_semantic_cache Introduction](docs/index.md)
- [pg_semantic_cache Architecture](docs/architecture.md)
- [pg_semantic_cache Use Cases](docs/use_cases.md)
- [Quick Start](#quick-start)
- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Deploying in a Production Environment](docs/deployment.md)
- [Using pg_semantic_cache Functions](docs/functions.md)
- [Sample Integrations](docs/integration.md)
- [Monitoring](docs/logging.md)
- [Performance and Benchmarking](docs/performance.md)
- [Logging](docs/logging.md)
- [Troubleshooting](docs/troubleshooting.md)
- [FAQ](docs/FAQ.md)
- [Developers](docs/development.md)

For comprehensive documentation, visit [docs.pgedge.com](https://docs.pgedge.com).

`pg_semantic_cache` enables **semantic query result caching** for
PostgreSQL. Unlike traditional caching that requires exact query matches,
this extension uses vector embeddings to find and retrieve cached results
for semantically similar queries.

## Quick Start

The following steps walk you through installing and configuring the extension.

1. Install the required dependencies for your operating system.

   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql-16 postgresql-server-dev-16 postgresql-16-pgvector

   # Rocky Linux/RHEL
   sudo dnf install postgresql16 postgresql16-devel postgresql16-contrib

   # macOS (with Homebrew)
   brew install postgresql@16
   # Install pgvector separately
   ```

2. Build and install the extension from source.

   ```bash
   git clone https://github.com/pgedge/pg_semantic_cache.git
   cd pg_semantic_cache

   make clean && make
   sudo make install
   ```

3. Enable the extension in your PostgreSQL database.

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


## Basic Usage

The following examples demonstrate the core workflow for storing, retrieving,
and monitoring cached query results.

1. Store a query result with its vector embedding in the cache.

   In the following example, the `cache_query` function stores a completed
   orders query with a one-hour TTL and analytics tags.

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

2. Retrieve a cached result using semantic similarity search.

   In the following example, the `get_cached_result` function searches for
   cached results with at least 95% similarity to the query embedding.

   ```sql
   SELECT * FROM semantic_cache.get_cached_result(
       embedding            := '[0.11, 0.19, 0.31, ...]'::text,  -- Similar query embedding
       similarity_threshold := 0.95,                              -- 95% similarity required
       max_age_seconds      := NULL                               -- Any age (optional)
   );
   -- Returns: (found boolean, result_data jsonb, similarity_score float4, age_seconds int)
   ```

   The function returns a table with the following columns:

   ```
    found |        result_data         | similarity_score | age_seconds
   -------+----------------------------+------------------+-------------
    true  | {"total": 150, "orders"... | 0.973            | 245
   ```

3. Monitor cache performance using built-in statistics and health views.

   In the following example, the queries retrieve comprehensive statistics,
   health metrics, and recent activity for the semantic cache.

   ```sql
   -- Comprehensive statistics
   SELECT * FROM semantic_cache.cache_stats();

   -- Health overview (includes hit rate and more details)
   SELECT * FROM semantic_cache.cache_health;

   -- Recent cache activity
   SELECT * FROM semantic_cache.recent_cache_activity LIMIT 10;
   ```


## Building the Documentation

Before building the documentation, install Python 3.8+ and pip.

1. Install dependencies:
   ```bash
   pip install -r docs-requirements.txt
   ```

2. Use the following command to review the documentation locally:
   ```bash
   mkdocs serve
   ```

   Then open http://127.0.0.1:8000 in your browser.

3. To build a static site:
   ```bash
   mkdocs build
   ```

   Documentation will added to the `site/` directory.

---

## Support & Resources

To report an issue with this software, visit the
[GitHub Issues](https://github.com/pgEdge/pg_semantic_cache/issues) page.

Check the `examples/` directory for usage patterns and code samples; see
the `test/` directory for comprehensive testing examples.

For more information, visit [docs.pgedge.com](https://docs.pgedge.com).

## Contributing

We welcome your project contributions; for more information, see
[docs/development.md](docs/development.md).

---

## License

This project is licensed under the [PostgreSQL License](docs/LICENSE.md).

