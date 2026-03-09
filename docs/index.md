# pg_semantic_cache

pg_semantic_cache is a PostgreSQL extension that implements semantic query
result caching using vector embeddings. Unlike traditional query caching that
relies on exact string matching, pg_semantic_cache understands the *meaning*
of queries through vector similarity, enabling cache hits even when queries
are phrased differently.

This extension is particularly valuable for:

- AI/LLM applications can cache expensive LLM API calls and RAG (Retrieval
  Augmented Generation) results.
- Analytics workloads can reuse results from complex analytical queries with
  similar parameters.
- External API queries can cache results from expensive external data
  sources.
- Database query optimization can reduce load on expensive database
  operations.

### Why Use Semantic Caching

Semantic caching transforms how applications handle query results by
using vector matching rather than matching exact queries. Traditional caching
systems can miss cached result sets when queries are phrased differently,
while semantic caching recognizes that "What was Q4 revenue?" and "Show Q4 revenue" as the same question. This approach dramatically increases cache hit rates
and reduces costs for AI applications, analytics workloads, and external API
calls.

Queries that would overlook cached result sets work with a semantic cache:

| Traditional Cache | Semantic Cache |
|-------------------|----------------|
| "What was Q4 revenue?" ❌ Miss | "What was Q4 revenue?" ✅ Hit |
| "Show Q4 revenue" ❌ Miss | "Show Q4 revenue" ✅ Hit |
| "Q4 revenue please" ❌ Miss | "Q4 revenue please" ✅ Hit |

### Cost Savings Example

For an LLM application making 10,000 queries per day:

- Without caching costs $200/day (at $0.02 per query).
- With 80% cache hit rate costs $40/day.
- Savings are $160/day or $58,400/year.

### Key Features

- Semantic matching uses pgvector for similarity-based cache lookups.
- Flexible TTL provides per-entry time-to-live configuration.
- Tag-based management organizes and invalidates cache entries by tags.
- Multiple eviction policies include LRU, LFU, and TTL-based automatic
  eviction.
- Cost tracking monitors and reports on query cost savings.
- Configurable dimensions support various embedding models (768, 1536,
  3072+ dimensions).
- Multiple index types include IVFFlat (fast) or HNSW (accurate) vector
  indexes.
- Comprehensive monitoring provides built-in statistics, views, and health
  metrics.

### Cross-Platform Support

The extension is fully compatible with all PostgreSQL-supported platforms.

Fully compatible with all PostgreSQL-supported platforms:

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Supported | Ubuntu, Debian, RHEL, Rocky, Fedora, etc. |
| macOS | Supported | Intel & Apple Silicon |
| Windows | Supported | Via MinGW or MSVC |
| BSD | Supported | FreeBSD, OpenBSD |

