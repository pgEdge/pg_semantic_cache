# pg_semantic_cache

The pg_semantic_cache extension implements semantic query result caching
using vector embeddings. Unlike traditional query caching that relies on
exact string matching, pg_semantic_cache understands the meaning of queries
through vector similarity. The extension enables cache hits even when
queries are phrased differently.

The extension is particularly valuable for the following use cases:

- AI and LLM applications can cache expensive LLM API calls and RAG results.
- Analytics workloads can reuse results from complex analytical queries.
- External API queries can cache results from expensive external sources.
- Database query optimization can reduce load on expensive operations.

## Why Use Semantic Caching

Semantic caching transforms how applications handle query results by using
vector matching rather than matching exact queries. Traditional caching
systems can miss cached result sets when queries are phrased differently.
Semantic caching recognizes that "What was Q4 revenue?" and "Show Q4
revenue" represent the same question. This approach dramatically increases
cache hit rates and reduces costs for AI applications.

The following table shows queries that would overlook cached result sets
with traditional caching but work with a semantic cache:

| Traditional Cache | Semantic Cache |
|-------------------|----------------|
| "What was Q4 revenue?" ❌ Miss | "What was Q4 revenue?" ✅ Hit |
| "Show Q4 revenue" ❌ Miss | "Show Q4 revenue" ✅ Hit |
| "Q4 revenue please" ❌ Miss | "Q4 revenue please" ✅ Hit |

## Cost Savings Example

For an LLM application making 10,000 queries per day, semantic caching can
provide significant cost savings. The following example demonstrates the
potential savings:

- Without caching, the application costs $200 per day (at $0.02 per query).
- With an 80% cache hit rate, the application costs $40 per day.
- The savings are $160 per day or $58,400 per year.

## Key Features

The pg_semantic_cache extension includes the following features:

- Semantic matching uses pgvector for similarity-based cache lookups.
- Flexible TTL provides per-entry time-to-live configuration.
- Tag-based management organizes and invalidates cache entries by tags.
- Multiple eviction policies include LRU, LFU, and TTL-based eviction.
- Cost tracking monitors and reports on query cost savings.
- Configurable dimensions support various embedding models.
- Multiple index types include IVFFlat (fast) or HNSW (accurate) indexes.
- Comprehensive monitoring provides built-in statistics and health metrics.

## Cross-Platform Support

The extension is fully compatible with all PostgreSQL-supported platforms.
The following table shows the platform support status:

| Platform | Status | Notes |
|----------|--------|-------|
| Linux | Supported | Ubuntu, Debian, RHEL, Rocky, Fedora, etc. |
| macOS | Supported | Intel & Apple Silicon |
| Windows | Supported | Via MinGW or MSVC |
| BSD | Supported | FreeBSD, OpenBSD |
