# Performance and Benchmarking

The extension is optimized for sub-millisecond cache lookups with minimal overhead.

- Lookup time is < 5ms for most queries with IVFFlat index.
- Scalability handles 100K+ cached entries efficiently.
- Throughput reaches thousands of cache lookups per second.
- Storage provides configurable cache size limits with automatic eviction.

!!! tip "Pro Tip"

    Start with the default IVFFlat index and 1536 dimensions (OpenAI
    ada-002). You can always reconfigure your cache later with the
    `set_vector_dimension()` and `rebuild_index()` functions.

## Runtime Metrics

The following table shows typical performance metrics for common cache operations.

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Cache lookup | **< 5ms** | With optimized vector index |
| Cache insert | **< 10ms** | Including embedding storage |
| Eviction (1000 entries) | **< 50ms** | Efficient batch operations |
| Statistics query | **< 1ms** | Materialized views |
| Similarity search | **2-3ms avg** | IVFFlat/HNSW indexed |

### Expected Hit Rates

Cache hit rates vary by workload type and query similarity patterns.

| Workload Type | Typical Hit Rate |
|---------------|------------------|
| AI/LLM queries | 40-60% |
| Analytics dashboards | 60-80% |
| Search systems | 50-70% |
| Chatbot conversations | 45-65% |

### Memory Overhead

The cache maintains a minimal memory footprint for typical workloads.

- Each cache entry requires approximately 1-2KB for metadata and indexes.
- Vector storage size depends on the embedding dimension (1536D requires approximately 6KB).
- The total overhead remains minimal for typical workloads.

## Benchmarking

The extension includes a comprehensive benchmark suite for performance testing.

Use the following command to run the included benchmark suite:

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




