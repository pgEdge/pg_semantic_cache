# Using pg_semantic_cache Functions

The extension provides a complete set of SQL functions for caching,
eviction, monitoring, and configuration. This page provides a
comprehensive reference for all available functions in the
pg_semantic_cache extension.

## Function Reference

The pg_semantic_cache extension includes the following functions:

| Function | Description |
|----------|-------------|
| [auto_evict](functions/auto_evict.md) | Automatically evicts entries based on configured policy (LRU, LFU, or TTL). |
| [cache_hit_rate](functions/cache_hit_rate.md) | Gets the current cache hit rate as a percentage. |
| [cache_query](functions/cache_query.md) | Stores a query result with the vector embedding in the cache. |
| [cache_stats](functions/cache_stats.md) | Gets comprehensive cache statistics including hits, misses, and hit rate. |
| [clear_cache](functions/clear_cache.md) | Removes all cache entries (use with caution). |
| [evict_expired](functions/evict_expired.md) | Removes all expired cache entries based on TTL. |
| [evict_lfu](functions/evict_lfu.md) | Evicts least frequently used entries, keeping only the specified count. |
| [evict_lru](functions/evict_lru.md) | Evicts least recently used entries, keeping only the specified count. |
| [get_cached_result](functions/get_cached_result.md) | Retrieves a cached result by semantic similarity search. |
| [get_cost_savings](functions/get_cost_savings.md) | Calculates the estimated cost savings from cache usage. |
| [get_index_type](functions/get_index_type.md) | Gets the current vector index type (IVFFlat or HNSW). |
| [get_vector_dimension](functions/get_vector_dimension.md) | Gets the current vector embedding dimension. |
| [init_schema](functions/init_schema.md) | Initializes the cache schema and creates required tables, indexes, and views. |
| [invalidate_cache](functions/invalidate_cache.md) | Invalidates cache entries by pattern matching or tags. |
| [log_cache_access](functions/log_cache_access.md) | Logs cache access events for debugging and analysis. |
| [rebuild_index](functions/rebuild_index.md) | Rebuilds the vector similarity index for optimal performance. |
| [set_index_type](functions/set_index_type.md) | Sets the vector index type for similarity search. |
| [set_vector_dimension](functions/set_vector_dimension.md) | Sets the vector embedding dimension. |

## Core Functions

The core functions initialize the cache and manage query storage and
retrieval.

### init_schema()

The `init_schema()` function initializes the cache schema and creates all
required tables, indexes, and views.

In the following example, the `init_schema()` function sets up the
semantic cache infrastructure:

```sql
SELECT semantic_cache.init_schema();
```

### cache_query(query_text, embedding, result_data, ttl_seconds, tags)

The `cache_query()` function stores a query result with the corresponding
vector embedding for future retrieval.

**Parameters:**

- `query_text` (text) - The original query text
- `embedding` (text) - Vector embedding as text: `'[0.1, 0.2, ...]'`
- `result_data` (jsonb) - The query result to cache
- `ttl_seconds` (int) - Time-to-live in seconds
- `tags` (text[]) - Optional tags for organization

**Returns:** `bigint` - Cache entry ID

### get_cached_result(embedding, similarity_threshold, max_age_seconds)

The `get_cached_result()` function retrieves a cached result by semantic
similarity.

**Parameters:**

- `embedding` (text) - Query embedding to search for
- `similarity_threshold` (float4) - Minimum similarity (0.0 to 1.0)
- `max_age_seconds` (int) - Maximum age in seconds (NULL = any age)

**Returns:** `record` - `(found boolean, result_data jsonb,
similarity_score float4, age_seconds int)`

## Cache Eviction

Multiple eviction strategies are available to manage cache size and
freshness. The extension supports TTL-based, LRU, LFU, and automatic
eviction policies.

### evict_expired()

The `evict_expired()` function removes all expired cache entries.

In the following example, the `evict_expired()` function removes entries
that have exceeded their TTL:

```sql
SELECT semantic_cache.evict_expired();
```

The function returns the count of evicted entries.

### evict_lru(keep_count)

The `evict_lru()` function evicts least recently used entries and keeps
only the specified number of most recent entries.

In the following example, the `evict_lru()` function keeps only the 1000
most recently used entries:

```sql
SELECT semantic_cache.evict_lru(1000);
```

### evict_lfu(keep_count)

The `evict_lfu()` function evicts least frequently used entries and keeps
only the specified number of most frequently used entries.

In the following example, the `evict_lfu()` function keeps only the 1000
most frequently used entries:

```sql
SELECT semantic_cache.evict_lfu(1000);
```

### auto_evict()

The `auto_evict()` function automatically evicts entries based on the
configured policy (LRU, LFU, or TTL).

In the following example, the `auto_evict()` function applies the
configured eviction policy:

```sql
SELECT semantic_cache.auto_evict();
```

### clear_cache()

The `clear_cache()` function removes all cache entries. Use this function
with caution in production environments.

In the following example, the `clear_cache()` function removes all cached
entries:

```sql
SELECT semantic_cache.clear_cache();
```

## Statistics and Monitoring

Built-in functions and views provide real-time visibility into cache
performance. The extension tracks hits, misses, and overall cache health.

### cache_stats()

The `cache_stats()` function returns comprehensive cache statistics.

In the following example, the `cache_stats()` function retrieves current
cache performance metrics:

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

For more detailed statistics including cache size, expired entries, and
access patterns, use the `semantic_cache.cache_health` view.
