# Security Audit Report - pg_semantic_cache Extension

**Date**: 2024-12-18
**Version**: 0.1.0-beta4
**Auditor**: Security Review Process

---

## Executive Summary

This security audit reviews the pg_semantic_cache PostgreSQL extension for common vulnerabilities including SQL injection, buffer overflows, input validation issues, and PostgreSQL-specific security concerns.

**Overall Risk Level**: LOW-MEDIUM
**Critical Issues**: 1 (SQL Injection vulnerability)
**High Issues**: 0
**Medium Issues**: 2
**Low Issues**: 3

---

## Critical Issues

### 1. SQL Injection Vulnerability in Query Construction

**Location**: `pg_semantic_cache.c:365-373` (evict_lru), `pg_semantic_cache.c:400-408` (evict_lfu), `pg_semantic_cache.c:260-270` (get_cached_result)

**Issue**: User-controlled integer is used in SQL query construction via `appendStringInfo` without proper parameterization.

```c
// VULNERABLE CODE (lines 366-373)
appendStringInfo(&buf,
    "DELETE FROM semantic_cache.cache_entries "
    "WHERE id NOT IN ("
    "  SELECT id FROM semantic_cache.cache_entries "
    "  ORDER BY last_accessed_at DESC "
    "  LIMIT %d"    // ← Integer format, but what if keep_count is manipulated?
    ")",
    keep_count);
```

**Risk**: While `%d` format specifier for integers provides some protection, the value is not properly validated before use.

**Status**: ✅ **MITIGATED** - Input validation added (lines 357-363, 392-398)
```c
if (keep_count < 0)
    elog(ERROR, "evict_lru: keep_count must be non-negative");
```

**Remaining Concern**: No upper bound validation (could cause performance issues with very large values)

**Recommendation**:
```c
if (keep_count < 0 || keep_count > 1000000)
    elog(ERROR, "evict_lru: keep_count must be between 0 and 1000000");
```

---

### 2. String Escaping Function - Potential Issues

**Location**: `pg_semantic_cache.c:45-76` (pg_escape_string)

**Issue**: Custom string escaping function instead of using PostgreSQL's built-in functions.

```c
static char *
pg_escape_string(const char *str)
{
    size_t len = strlen(str);
    char *result = palloc(len * 2 + 3);  // Allocates enough space
    // ... manual escaping logic
}
```

**Risk**: Custom escaping is error-prone. PostgreSQL provides `quote_literal_cstr()` for this purpose.

**Status**: ⚠️ **NEEDS REVIEW**

**Recommendation**: Replace with PostgreSQL's built-in functions:
```c
#include "utils/quote.h"
// Use quote_literal_cstr(str) instead of pg_escape_string(str)
```

---

## High Issues

None identified.

---

## Medium Issues

### 3. Unbounded String Concatenation

**Location**: `pg_semantic_cache.c:161-200` (cache_query)

**Issue**: Large JSONB results are converted to strings and concatenated without size limits.

```c
rstr = JsonbToCString(NULL, &result->root, VARSIZE(result));
// No size check before using rstr
```

**Risk**: Very large JSONB documents could cause memory exhaustion.

**Recommendation**:
```c
if (strlen(rstr) > 10 * 1024 * 1024)  // 10MB limit
    elog(ERROR, "Result data too large (max 10MB)");
```

### 4. Missing NULL Checks in Helper Functions

**Location**: `pg_semantic_cache.c:38-43` (execute_sql)

**Issue**: No NULL check on input parameter.

```c
static void execute_sql(const char *query)
{
    int ret = SPI_execute(query, false, 0);
    // What if query is NULL?
}
```

**Recommendation**:
```c
static void execute_sql(const char *query)
{
    if (query == NULL)
        elog(ERROR, "execute_sql: query is NULL");
    int ret = SPI_execute(query, false, 0);
    if (ret < 0)
        elog(ERROR, "SPI_execute failed: %d", ret);
}
```

---

## Low Issues

### 5. Memory Leak Potential

**Location**: `pg_semantic_cache.c:165-238` (cache_query)

**Issue**: If error occurs after memory allocation, `pfree()` calls may be skipped.

**Current Code**:
```c
qstr = text_to_cstring(query_text);
estr = text_to_cstring(emb_text);
rstr = JsonbToCString(NULL, &result->root, VARSIZE(result));
// ... lots of code that could error ...
pfree(qstr);  // Only freed at the end
```

**Status**: ✅ **LOW RISK** - PostgreSQL's memory context system will clean up on error.

**Recommendation**: Use `PG_TRY/PG_CATCH` for explicit cleanup in critical paths.

### 6. Integer Overflow in String Length Calculation

**Location**: `pg_semantic_cache.c:194-200`

**Issue**: `strlen(rstr)` result is cast to `int` without overflow check.

```c
appendStringInfo(&buf,
    // ...
    "%d, %d, "  // result_size_bytes
    // ...
    (int)strlen(rstr), ttl, ttl);
```

**Risk**: If `rstr` length exceeds INT_MAX, the cast will overflow.

**Recommendation**:
```c
size_t result_len = strlen(rstr);
if (result_len > INT_MAX)
    elog(ERROR, "Result data too large");
int result_size = (int)result_len;
```

### 7. SPI Error Handling Inconsistency

**Location**: Multiple locations

**Issue**: Some SPI operations check return codes, others don't.

**Examples**:
- ✅ Good: `pg_semantic_cache.c:217-218` checks `ret < 0`
- ⚠️ Inconsistent: `pg_semantic_cache.c:279` doesn't check SPI_connect result
- ⚠️ Inconsistent: `pg_semantic_cache.c:321` checks SELECT result but not all operations

**Recommendation**: Standardize SPI error handling:
```c
if (SPI_connect() != SPI_OK_CONNECT)
    elog(ERROR, "SPI_connect failed");
// ... do work ...
if (SPI_finish() != SPI_OK_FINISH)
    elog(WARNING, "SPI_finish failed");
```

---

## Input Validation Summary

### ✅ Well-Validated Inputs

1. **evict_lru/evict_lfu**: Checks for NULL and negative values
2. **get_cost_savings**: Uses default for NULL days parameter
3. **cache_query**: Checks for NULL tags parameter

### ⚠️ Needs Validation

1. **Embedding vectors**: No dimension validation (assumes 1536)
2. **Similarity thresholds**: No range check (should be 0.0-1.0)
3. **TTL values**: No upper bound (could be set to extreme values)
4. **JSONB result size**: No size limit

---

## Recommendations

### Immediate Actions (P0)

1. ✅ **Replace custom escaping** with PostgreSQL's `quote_literal_cstr()`
2. ✅ **Add upper bounds** to eviction function parameters
3. ✅ **Add result size limits** for cached data

### Short-term (P1)

4. **Validate embedding dimensions** against expected size
5. **Validate similarity thresholds** (0.0 - 1.0 range)
6. **Standardize SPI error handling**

### Long-term (P2)

7. **Add rate limiting** for cache writes
8. **Implement query allowlisting** for production use
9. **Add encryption** for sensitive cached data
10. **Add audit logging** for security events

---

## Code Fixes

### Fix 1: Replace Custom Escaping

```c
// BEFORE
#include "utils/builtins.h"

static char *
pg_escape_string(const char *str)
{
    // ... custom escaping logic ...
}

// AFTER
#include "utils/builtins.h"
#include "utils/quote.h"

// Remove pg_escape_string function entirely
// Use quote_literal_cstr() directly:
char *escaped = quote_literal_cstr(qstr);
```

### Fix 2: Add Input Validation Function

```c
static void validate_similarity_threshold(float4 threshold)
{
    if (threshold < 0.0 || threshold > 1.0)
        elog(ERROR, "Similarity threshold must be between 0.0 and 1.0");
}

static void validate_ttl(int32 ttl)
{
    if (ttl < 0)
        elog(ERROR, "TTL must be non-negative");
    if (ttl > 86400 * 365)  // 1 year max
        elog(ERROR, "TTL exceeds maximum (1 year)");
}

static void validate_embedding_size(text *embedding_text)
{
    char *emb_str = text_to_cstring(embedding_text);
    // Parse and count dimensions
    // Ensure it matches expected vector size
    pfree(emb_str);
}
```

### Fix 3: Standardized Error Handling

```c
#define SPI_CONNECT_OR_ERROR() \
    do { \
        if (SPI_connect() != SPI_OK_CONNECT) \
            elog(ERROR, "%s: SPI_connect failed", __func__); \
    } while(0)

#define SPI_FINISH_OR_WARN() \
    do { \
        if (SPI_finish() != SPI_OK_FINISH) \
            elog(WARNING, "%s: SPI_finish failed", __func__); \
    } while(0)
```

---

## Security Testing Checklist

- [x] SQL injection attempts (integers, strings)
- [x] NULL input handling
- [x] Negative value handling
- [ ] Extremely large values (INT_MAX, LONG_MAX)
- [ ] Very long strings (> 1GB)
- [ ] Malformed embeddings
- [ ] Concurrent access testing
- [ ] Resource exhaustion testing
- [ ] Privilege escalation attempts

---

## Conclusion

The pg_semantic_cache extension has **reasonable security** for a prototype but requires **hardening for production use**. The main concerns are:

1. Custom string escaping should be replaced with PostgreSQL built-ins
2. Input validation should be more comprehensive
3. Resource limits should be enforced

**Recommended Actions Before Production**:
1. Implement all P0 fixes
2. Add comprehensive fuzz testing
3. Perform load testing with malicious inputs
4. Add security documentation for users
5. Consider third-party security audit

---

**Next Review Date**: Before 1.0.0 release
**Status**: CONDITIONALLY APPROVED for development use
**Production Readiness**: BLOCKED pending P0 fixes
