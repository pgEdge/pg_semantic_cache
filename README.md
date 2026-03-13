# pg_semantic_cache

pg_semantic_cache allows you to leverage vector embeddings to cache and
retrieve query results based on semantic similarity.

## Table of Contents

- [Overview](docs/index.md)
- [Architecture](docs/architecture.md)
- [Use Cases](docs/use_cases.md)
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

The following steps walk you through installing and configuring the
extension.

1. Install the required dependencies for your operating system.

   In the following example, the commands install dependencies on
   Ubuntu, Rocky Linux, or macOS:

   ```bash
   sudo apt-get install postgresql-16 postgresql-server-dev-16 \
       postgresql-16-pgvector

   sudo dnf install postgresql16 postgresql16-devel postgresql16-contrib

   brew install postgresql@16
   ```

2. Build and install the extension from source.

   In the following example, the commands clone the repository, build
   the extension, and install it:

   ```bash
   git clone https://github.com/pgedge/pg_semantic_cache.git
   cd pg_semantic_cache

   make clean && make
   sudo make install
   ```

3. Enable the extension in your PostgreSQL database.

   In the following example, the SQL commands create the required
   extensions and initialize the cache schema:

   ```sql
   psql -U postgres -d your_database

   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

   SELECT semantic_cache.init_schema();

   SELECT * FROM semantic_cache.cache_stats();
   ```

### Configuration

All runtime settings can be configured through the cache configuration
table.

Configuration settings are stored in the `semantic_cache.cache_config`
table.

In the following example, the SQL commands view and modify
configuration settings:

```sql
SELECT * FROM semantic_cache.cache_config ORDER BY key;

INSERT INTO semantic_cache.cache_config (key, value)
VALUES ('max_cache_size_mb', '2000')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

SELECT value FROM semantic_cache.cache_config
WHERE key = 'eviction_policy';
```

The following table describes common configuration keys:

| Key | Example Value | Description |
|-----|---------------|-------------|
| max_cache_size_mb | 1000 | Maximum cache size in megabytes |
| default_ttl_seconds | 3600 | Default TTL for cached entries |
| eviction_policy | lru | Eviction policy |
| similarity_threshold | 0.95 | Default similarity threshold |


## Basic Usage

The following examples demonstrate the core workflow for storing,
retrieving, and monitoring cached query results.

In the following example, the `cache_query` function stores a
completed orders query with a one-hour TTL and analytics tags:

```sql
SELECT semantic_cache.cache_query(
    query_text    := 'SELECT * FROM orders WHERE status = ''completed''',
    embedding     := '[0.1, 0.2, 0.3, ...]'::text,
    result_data   := '{"total": 150, "orders": [...]}'::jsonb,
    ttl_seconds   := 3600,
    tags          := ARRAY['orders', 'analytics']
);
```

In the following example, the `get_cached_result` function searches
for cached results with at least 95 percent similarity to the query
embedding:

```sql
SELECT * FROM semantic_cache.get_cached_result(
    embedding            := '[0.11, 0.19, 0.31, ...]'::text,
    similarity_threshold := 0.95,
    max_age_seconds      := NULL
);
```

The function returns a table with the following columns:

```
 found |        result_data         | similarity_score | age_seconds
-------+----------------------------+------------------+-------------
 true  | {"total": 150, "orders"... | 0.973            | 245
```

In the following example, the queries retrieve comprehensive
statistics, health metrics, and recent activity for the semantic
cache:

```sql
SELECT * FROM semantic_cache.cache_stats();

SELECT * FROM semantic_cache.cache_health;

SELECT * FROM semantic_cache.recent_cache_activity LIMIT 10;
```


## Building the Documentation

Before building the documentation, install Python 3.8 or later and
pip.

In the following example, the command installs documentation
dependencies:

```bash
pip install -r docs-requirements.txt
```

In the following example, the command starts a local documentation
server:

```bash
mkdocs serve
```

Open http://127.0.0.1:8000 in your browser to view the documentation.

In the following example, the command builds a static documentation
site:

```bash
mkdocs build
```

Documentation will be added to the `site/` directory.

## Support and Resources

To report an issue with this software, visit the
[GitHub Issues](https://github.com/pgEdge/pg_semantic_cache/issues)
page.

Check the `examples/` directory for usage patterns and code samples.
See the `test/` directory for comprehensive testing examples.

For more information, visit [docs.pgedge.com](https://docs.pgedge.com).

## Contributing

We welcome your project contributions. For more information, see
[docs/development.md](docs/development.md).

## License

This project is licensed under the
[PostgreSQL License](docs/LICENSE.md).

