# Installation

This guide covers installing pg_semantic_cache from source on various platforms.

## Prerequisites

### Required

- **PostgreSQL**: Version 14, 15, 16, 17, or 18
- **pgvector**: Must be installed before pg_semantic_cache
- **C Compiler**: gcc or clang
- **make**: GNU Make or compatible
- **PostgreSQL Development Headers**: Required for building extensions

### Platform-Specific Packages

=== "Debian/Ubuntu"
    ```bash
    sudo apt-get install -y \
        postgresql-server-dev-17 \
        build-essential \
        git

    # Install pgvector (if not already installed)
    cd /tmp
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    ```

=== "RHEL/Rocky/AlmaLinux"
    ```bash
    sudo yum install -y \
        postgresql17-devel \
        gcc \
        make \
        git

    # Install pgvector (if not already installed)
    cd /tmp
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    ```

=== "macOS"
    ```bash
    # Using Homebrew
    brew install postgresql@17

    # Ensure pg_config is in PATH
    export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

    # Install pgvector (if not already installed)
    cd /tmp
    git clone https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    make install
    ```

## Building from Source

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/pgEdge/pg_semantic_cache.git
cd pg_semantic_cache

# Build
make clean
make

# Install (requires appropriate permissions)
sudo make install
```

### Multi-Version PostgreSQL

If you have multiple PostgreSQL versions installed:

```bash
# Specify pg_config explicitly
PG_CONFIG=/usr/pgsql-17/bin/pg_config make clean install

# Or build for multiple versions
for PG in 14 15 16 17 18; do
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```

### Development Build

For development with verbose output:

```bash
make dev-install
```

### View Build Configuration

```bash
make info
```

Output includes:
- PostgreSQL version and paths
- Compiler and flags
- Installation directories
- Extension version

## Verifying Installation

### Check Extension Files

```bash
# Verify shared library is installed
ls -lh $(pg_config --pkglibdir)/pg_semantic_cache.so

# Verify control file is installed
ls -lh $(pg_config --sharedir)/extension/pg_semantic_cache.control

# Verify SQL installation file
ls -lh $(pg_config --sharedir)/extension/pg_semantic_cache--*.sql
```

### Check pgvector Installation

```bash
# pgvector must be installed first
ls -lh $(pg_config --pkglibdir)/vector.so
```

## PostgreSQL Configuration

### Update postgresql.conf

pg_semantic_cache works out of the box without special configuration, but for optimal performance with large caches:

```ini
# Recommended for production with large caches
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
work_mem = 256MB                        # For vector operations
maintenance_work_mem = 1GB              # For index creation

# Enable query timing (optional, for monitoring)
track_io_timing = on
```

Restart PostgreSQL after configuration changes:

```bash
# Systemd
sudo systemctl restart postgresql

# Or using pg_ctl
pg_ctl restart -D /var/lib/postgresql/data
```

## Creating the Extension

### In psql

```sql
-- Connect to your database
\c your_database

-- Install pgvector (required dependency)
CREATE EXTENSION IF NOT EXISTS vector;

-- Install pg_semantic_cache
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_semantic_cache');
```

Expected output:
```
      extname       | extversion
--------------------+------------
 vector             | 0.7.0
 pg_semantic_cache  | 0.1.0-beta4
```

### Verify Schema Creation

```sql
-- Check that schema and tables were created
\dt semantic_cache.*

-- View cache health
SELECT * FROM semantic_cache.cache_health;
```

## Troubleshooting Installation

### pg_config not found

```bash
# Find PostgreSQL installation
sudo find / -name pg_config 2>/dev/null

# Add to PATH
export PATH="/usr/pgsql-17/bin:$PATH"

# Or specify directly
PG_CONFIG=/path/to/pg_config make install
```

### Permission Denied During Installation

```bash
# Use sudo for system directories
sudo make install

# Or install to custom directory (no sudo required)
make install DESTDIR=/path/to/custom/location
```

### pgvector Not Found

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

### Extension Already Exists

```sql
-- If you're upgrading, drop the old version first
DROP EXTENSION IF EXISTS pg_semantic_cache CASCADE;

-- Then reinstall
CREATE EXTENSION pg_semantic_cache;
```

!!! warning "Data Loss Warning"
    Dropping the extension will delete all cached data. Use `ALTER EXTENSION UPDATE` for upgrades when available.

### Compilation Errors

```bash
# Ensure development headers are installed
# Debian/Ubuntu
sudo apt-get install postgresql-server-dev-17

# RHEL/Rocky
sudo yum install postgresql17-devel

# Verify pg_config works
pg_config --includedir-server
```

## Testing Installation

Run the included test suite:

```bash
# Requires a running PostgreSQL instance
make installcheck
```

Or run manual tests:

```sql
-- Load example tests
\i examples/usage_examples.sql

-- Run benchmarks
\i test/benchmark.sql
```

## Uninstalling

### Remove Extension from Database

```sql
DROP EXTENSION IF EXISTS pg_semantic_cache CASCADE;
```

### Remove Files from System

```bash
cd pg_semantic_cache
sudo make uninstall
```

This removes:
- Shared library (`.so` file)
- Control file
- SQL installation files

## Next Steps

- [Configuration](configuration.md) - Configure vector dimensions and index types
- [Functions Reference](functions/index.md) - Learn about available functions
- [Use Cases](use_cases.md) - See practical examples
