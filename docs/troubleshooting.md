# Troubleshooting Installation

The Troubleshooting page lists some common issues encountered during
installation, and how to resolve the problems.

## pg_config not found

The build system needs pg_config to locate PostgreSQL installation
paths. If pg_config is not in your PATH, the build will fail.

```bash
# Find PostgreSQL installation
sudo find / -name pg_config 2>/dev/null

# Add to PATH
export PATH="/usr/pgsql-17/bin:$PATH"

# Or specify directly
PG_CONFIG=/path/to/pg_config make install
```

## Permission Denied During Installation

Installing an extension requires write access to PostgreSQL's system
directories. Use sudo for standard installations or specify a custom
directory.

```bash
# Use sudo for system directories
sudo make install

# Or install to custom directory (no sudo required)
make install DESTDIR=/path/to/custom/location
```

## pgvector Not Found

The pg_semantic_cache extension depends on pgvector and will fail to
create if pgvector is not installed. You must install pgvector before
installing pg_semantic_cache.

```sql
-- Error: could not open extension control file
-- Solution: Install pgvector first
```

```bash
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

## Extension Already Exists

When reinstalling or upgrading, PostgreSQL may report that the
extension already exists. Drop the existing extension before creating
a new one.

```sql
-- If you're upgrading, drop the old version first
DROP EXTENSION IF EXISTS pg_semantic_cache CASCADE;

-- Then reinstall
CREATE EXTENSION pg_semantic_cache;
```

!!! warning "Data Loss Warning"
    Dropping the extension will delete all cached data. Use `ALTER
    EXTENSION UPDATE` for upgrades when available.

## Compilation Errors

Compilation failures typically occur when PostgreSQL development
headers are missing. Install the appropriate development package for
your platform.

```bash
# Ensure development headers are installed
# Debian/Ubuntu
sudo apt-get install postgresql-server-dev-17

# RHEL/Rocky
sudo yum install postgresql17-devel

# Verify pg_config works
pg_config --includedir-server
```
