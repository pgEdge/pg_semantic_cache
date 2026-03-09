# Using pg_semantic_cache Functions

This page provides a comprehensive reference for all available functions in the pg_semantic_cache extension.

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
