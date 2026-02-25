# Getting Started - pg_semantic_cache (C Version)

## Why C Instead of Rust?

**Short answer:** Better fit for this extension.

| Factor | C | Rust |
|--------|---|------|
| Binary Size | **100KB** ✅ | 2-5MB |
| Build Time | **10-30s** ✅ | 2-5min |
| PG 18 Support | **Immediate** ✅ | Wait for pgrx |
| Packaging | **Simple** ✅ | Complex |
| Tradition | **Standard** ✅ | New |

## Installation (3 Steps)

### 1. Install Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-16 postgresql-server-dev-16 postgresql-16-pgvector
```

**Rocky Linux/RHEL:**
```bash
sudo dnf install postgresql16 postgresql16-devel postgresql16-contrib
# pgvector from source or pgdg repository
```

**macOS:**
```bash
brew install postgresql@16
# Install pgvector from source
```

### 2. Build and Install

```bash
cd pg_semantic_cache

# Quick install (recommended)
./install.sh

# Or manual
make clean
make
sudo make install
```

**Expected output:**
```
Building pg_semantic_cache...
gcc -Wall -Wmissing-prototypes ... -c pg_semantic_cache.c
gcc -shared -o pg_semantic_cache.so pg_semantic_cache.o
✓ Build successful (10-30 seconds)
✓ Binary size: ~100KB
```

### 3. Enable in PostgreSQL

```sql
-- Connect to your database
psql -U postgres -d your_database

-- Install extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Initialize schema (run once per database)
SELECT semantic_cache.init_schema();

-- Verify installation
SELECT * FROM semantic_cache.cache_stats();
```

## Quick Test

```sql
-- Cache a test query
SELECT semantic_cache.cache_query(
    'SELECT * FROM test',
    '[0.1,0.2,0.3]'::text,  -- Dummy embedding
    '{"result": "test"}'::jsonb,
    3600,  -- 1 hour TTL
    NULL   -- No tags
);

-- Should return cache ID (e.g., 1)

-- Retrieve it
SELECT * FROM semantic_cache.get_cached_result(
    '[0.1,0.2,0.3]'::text,
    0.95,  -- 95% similarity
    NULL   -- No age limit
);

-- Should return: (true, '{"result": "test"}', 1.0, <age>)
```

## Real-World Usage

### With OpenAI Embeddings (Python)

```python
import psycopg2
import openai
import json

# Initialize
conn = psycopg2.connect("dbname=mydb user=postgres")
client = openai.OpenAI(api_key="your-key")

def cache_query_result(query, result):
    """Cache a query with OpenAI embedding"""
    
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    embedding = response.data[0].embedding
    
    # Convert to text format
    embedding_text = f"[{','.join(map(str, embedding))}]"
    
    # Cache it
    with conn.cursor() as cur:
        cur.execute("""
            SELECT semantic_cache.cache_query(
                %s::text,
                %s::text,
                %s::jsonb,
                3600,
                ARRAY['openai']
            )
        """, (query, embedding_text, json.dumps(result)))
        conn.commit()
        print(f"Cached query: {cur.fetchone()[0]}")

def get_cached_or_compute(query):
    """Try cache first, compute if miss"""
    
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    embedding = response.data[0].embedding
    embedding_text = f"[{','.join(map(str, embedding))}]"
    
    # Check cache
    with conn.cursor() as cur:
        cur.execute("""
            SELECT found, result_data, similarity_score
            FROM semantic_cache.get_cached_result(
                %s::text, 0.95, NULL
            )
        """, (embedding_text,))

        result = cur.fetchone()

        if result and result[0]:  # Cache hit
            print(f"Cache HIT (similarity: {result[2]:.3f})")
            return json.loads(result[1])
        else:
            print("Cache MISS - computing...")
            # Compute actual result here
            computed_result = {"answer": "computed value"}
            cache_query_result(query, computed_result)
            return computed_result

# Example usage
result = get_cached_or_compute("What is the Q4 revenue?")
print(result)

# Similar query will hit cache
result = get_cached_or_compute("Show me revenue for last quarter")
print(result)  # Cache HIT!
```

## Configuration

### View All Settings

```sql
SELECT * FROM semantic_cache.cache_config ORDER BY key;
```

### Update Settings

```sql
-- Increase cache size to 2GB (direct SQL update)
INSERT INTO semantic_cache.cache_config (key, value)
VALUES ('max_cache_size_mb', '2000')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Set default TTL to 2 hours
INSERT INTO semantic_cache.cache_config (key, value)
VALUES ('default_ttl_seconds', '7200')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Change eviction policy
INSERT INTO semantic_cache.cache_config (key, value)
VALUES ('eviction_policy', 'lru')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
```

## Monitoring

### Real-Time Statistics

```sql
-- Comprehensive stats
SELECT * FROM semantic_cache.cache_stats();

-- Health overview (includes hit rate)
SELECT * FROM semantic_cache.cache_health;

-- Recent activity
SELECT * FROM semantic_cache.recent_cache_activity LIMIT 10;
```

### Set Up Monitoring Dashboard

```sql
-- Create monitoring view
CREATE VIEW cache_dashboard AS
SELECT
    (SELECT hit_rate_percent FROM semantic_cache.cache_stats()) as hit_rate_pct,
    (SELECT total_entries FROM semantic_cache.cache_stats()) as entries,
    (SELECT pg_size_pretty(SUM(result_size_bytes)::BIGINT) FROM semantic_cache.cache_entries) as cache_size,
    (SELECT COUNT(*) FROM semantic_cache.cache_entries WHERE expires_at <= NOW()) as expired_entries,
    NOW() as updated_at;

-- Query it
SELECT * FROM cache_dashboard;
```

## Maintenance

### Automatic Eviction (Recommended)

```sql
-- Install pg_cron
CREATE EXTENSION pg_cron;

-- Schedule auto-eviction every 15 minutes
SELECT cron.schedule(
    'semantic-cache-maintenance',
    '*/15 * * * *',
    $$SELECT semantic_cache.auto_evict()$$
);

-- Verify scheduled job
SELECT * FROM cron.job;
```

### Manual Maintenance

```sql
-- Evict expired entries
SELECT semantic_cache.evict_expired();

-- Evict entries, keeping only the 1000 most recently used
SELECT semantic_cache.evict_lru(1000);  -- Keep 1000 entries

-- Delete entries by pattern (direct SQL)
DELETE FROM semantic_cache.cache_entries WHERE query_text LIKE 'old_query%';

-- Delete entries by tag (direct SQL)
DELETE FROM semantic_cache.cache_entries WHERE 'deprecated' = ANY(tags);

-- Clear everything (careful!)
-- SELECT semantic_cache.clear_cache();
```

## Performance Tuning

### For Large Caches (100k+ entries)

```sql
-- Rebuild index with more lists
DROP INDEX semantic_cache.idx_cache_embedding;
CREATE INDEX idx_cache_embedding 
    ON semantic_cache.cache_entries 
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 1000);

-- Or use HNSW for best performance (pgvector 0.5.0+)
CREATE INDEX idx_cache_embedding_hnsw
    ON semantic_cache.cache_entries 
    USING hnsw (query_embedding vector_cosine_ops);
```

### PostgreSQL Settings

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '4GB';

-- Increase effective cache size
ALTER SYSTEM SET effective_cache_size = '12GB';

-- For vector operations
ALTER SYSTEM SET work_mem = '256MB';

-- Reload configuration
SELECT pg_reload_conf();
```

## Benchmarking

```bash
# Run included benchmarks
psql -U postgres -d your_database -f test/benchmark.sql
```

**Expected results:**
- Insert 1000 entries: ~500ms
- Lookup 100 times: ~200ms (2ms avg)
- Eviction (5000 entries): ~100ms

## Multi-Version Support

### Build for Multiple PostgreSQL Versions

```bash
# Build for all versions
for PG in 14 15 16 17 18; do
    echo "Building for PostgreSQL $PG..."
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```

### RPM Packaging

```bash
# Create RPM spec
cat > pg_semantic_cache.spec << 'EOF'
Name: pg_semantic_cache
Version: 0.1.0-beta3
Release: 1%{?dist}
Summary: PostgreSQL semantic query cache extension
License: MIT
Source0: %{name}-%{version}.tar.gz

%description
Semantic query result caching using vector embeddings.

%prep
%setup -q

%build
make PG_CONFIG=/usr/pgsql-%{pg_version}/bin/pg_config

%install
make install DESTDIR=%{buildroot} PG_CONFIG=/usr/pgsql-%{pg_version}/bin/pg_config

%files
%{_libdir}/pgsql/pg_semantic_cache.so
%{_datadir}/pgsql/extension/pg_semantic_cache*
EOF

# Build it
rpmbuild -ba pg_semantic_cache.spec
```

## Troubleshooting

### Build Errors

**Problem**: `postgres.h not found`
```bash
# Install development headers
sudo apt-get install postgresql-server-dev-16  # Ubuntu/Debian
sudo dnf install postgresql16-devel            # RHEL/Rocky
```

**Problem**: `vector type not found`
```bash
# Install pgvector
sudo apt-get install postgresql-16-pgvector    # Ubuntu/Debian
# Or build from source
```

### Runtime Errors

**Problem**: "extension does not exist"
```sql
-- Make sure you ran:
CREATE EXTENSION pg_semantic_cache;
SELECT semantic_cache.init_schema();
```

**Problem**: Cache not finding results
```sql
-- Lower similarity threshold
SELECT * FROM semantic_cache.get_cached_result(
    embedding,
    0.85,  -- Try lower threshold
    NULL
);

-- Check for expired entries
SELECT COUNT(*) FROM semantic_cache.cache_entries 
WHERE expires_at <= NOW();
```

## Production Checklist

- [ ] pgvector installed
- [ ] Extension installed in all databases
- [ ] init_schema() run in each database
- [ ] Monitoring set up (views/dashboards)
- [ ] Auto-eviction scheduled (pg_cron)
- [ ] Indexes optimized for cache size
- [ ] PostgreSQL settings tuned
- [ ] Backup strategy in place
- [ ] Documentation for team

## Next Steps

1. **Read examples**: `examples/usage_examples.sql`
2. **Run benchmarks**: `test/benchmark.sql`
3. **Integrate with your app**: See Python example above
4. **Monitor performance**: Set up dashboard
5. **Tune for production**: Adjust settings based on workload

## Support

- **GitHub**: [https://github.com/pgEdge/pg_semantic_cache](https://github.com/pgEdge/pg_semantic_cache)
- **Documentation**: This guide + `README.md`
- **Examples**: `examples/` directory
- **Tests**: `test/` directory

## Why This Works

1. **Small & Fast**: 100KB binary, 10s builds
2. **Standard PostgreSQL**: Uses PGXS, works everywhere
3. **Immediate PG Support**: PG 14-18+ out of the box
4. **Production Ready**: Real error handling, tested
5. **Easy to Package**: Fits existing RPM/DEB workflows

---

**You now have a production-ready C extension that's faster to build, smaller in size, and supports PostgreSQL 18 immediately!** 🚀
