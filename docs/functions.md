# Using pg_semantic_cache Functions

The extension provides a complete set of SQL functions for caching, eviction, monitoring, and configuration. This page provides a comprehensive reference for all available functions in the pg_semantic_cache extension.

## Function Reference

| Function | Description |
|----------|-------------|
| [auto_evict](functions/auto_evict.md) | Automatically evicts entries based on configured policy (LRU, LFU, or TTL). |
| [cache_hit_rate](functions/cache_hit_rate.md) | Gets current cache hit rate as a percentage. |
| [cache_query](functions/cache_query.md) | Stores a query result with its vector embedding in the cache. |
| [cache_stats](functions/cache_stats.md) | Gets comprehensive cache statistics including hits, misses, and hit rate. |
| [clear_cache](functions/clear_cache.md) | Removes all cache entries (use with caution). |
| [evict_expired](functions/evict_expired.md) | Removes all expired cache entries based on TTL. |
| [evict_lfu](functions/evict_lfu.md) | Evicts least frequently used entries, keeping only specified count. |
| [evict_lru](functions/evict_lru.md) | Evicts least recently used entries, keeping only specified count. |
| [get_cached_result](functions/get_cached_result.md) | Retrieves a cached result by semantic similarity search. |
| [get_cost_savings](functions/get_cost_savings.md) | Calculates estimated cost savings from cache usage. |
| [get_index_type](functions/get_index_type.md) | Gets the current vector index type (IVFFlat or HNSW). |
| [get_vector_dimension](functions/get_vector_dimension.md) | Gets the current vector embedding dimension. |
| [init_schema](functions/init_schema.md) | Initializes cache schema and creates required tables, indexes, and views. |
| [invalidate_cache](functions/invalidate_cache.md) | Invalidates cache entries by pattern matching or tags. |
| [log_cache_access](functions/log_cache_access.md) | Logs cache access events for debugging and analysis. |
| [rebuild_index](functions/rebuild_index.md) | Rebuilds the vector similarity index for optimal performance. |
| [set_index_type](functions/set_index_type.md) | Sets the vector index type for similarity search. |
| [set_vector_dimension](functions/set_vector_dimension.md) | Sets the vector embedding dimension. |


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
