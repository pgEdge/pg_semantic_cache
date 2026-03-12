# Installation

You can install pg_semantic_cache from source on various platforms. Before 
installing pg_semantic_cache, you must install:

- PostgreSQL: Version 14, 15, 16, 17, or 18
- pgvector: Must be installed before pg_semantic_cache
- C Compiler: gcc or clang
- make: GNU Make or compatible
- PostgreSQL Development Headers: Required for building extensions

## Platform-Specific Packages

Use the following platform-specific commands to ensure that your host
is prepared for pg_semantic_cache:

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

You can use the following command to check your build environment and
configuration settings before compiling.

```bash
make info
```

Output includes the following information:

- The PostgreSQL version and paths.
- The compiler and flags.
- The installation directories.
- The extension version.

After configuring your build environment, build pg_semantic_cache using the
standard PostgreSQL extension build commands:

```bash
# Clone the repository
git clone https://github.com/pgedge/pg_semantic_cache.git
cd pg_semantic_cache

# Build
make clean
make

# Install (requires appropriate permissions)
sudo make install
```

A development build includes verbose output and debugging information; to
perform a development build, use the following command:

```bash
make dev-install
```

If you have multiple PostgreSQL versions installed, you can use PG_CONFIG to 
target specific PostgreSQL versions when multiple versions are installed.

```bash
# Specify pg_config explicitly
PG_CONFIG=/usr/pgsql-17/bin/pg_config make clean install

# Or build for multiple versions
for PG in 14 15 16 17 18; do
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```

### Verifying the Installation

After the installation completes, verify that all extension files are in
place.

Check for the extension files:

```bash
# Verify shared library is installed
ls -lh $(pg_config --pkglibdir)/pg_semantic_cache.so

# Verify control file is installed
ls -lh $(pg_config --sharedir)/extension/pg_semantic_cache.control

# Verify SQL installation file
ls -lh $(pg_config --sharedir)/extension/pg_semantic_cache--*.sql
```

Use the following command to confirm that pgvector is installed:

```bash
# pgvector must be installed first
ls -lh $(pg_config --pkglibdir)/vector.so
```

## Creating the Extension

Create the extension in your PostgreSQL database to begin using
semantic caching. Open the psql command line, and run the following
commands:

```sql
-- Connect to your database
\c your_database

-- Install pgvector (required dependency)
CREATE EXTENSION IF NOT EXISTS vector;

-- Install pg_semantic_cache
CREATE EXTENSION IF NOT EXISTS pg_semantic_cache;

-- Verify installation
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('vector', 'pg_semantic_cache');
```

Expected output:
```
      extname       | extversion
--------------------+------------
 vector             | 0.7.0
 pg_semantic_cache  | 0.1.0-beta3
```

### Verifying Schema Creation

Check that the semantic_cache schema and tables were created
successfully.

```sql
-- Check that schema and tables were created
\dt semantic_cache.*

-- View cache health
SELECT * FROM semantic_cache.cache_health;
```

## Optimizing the PostgreSQL Configuration

You can optimize PostgreSQL settings for better performance with semantic
caching by updating the `postgresql.conf` file.

The pg_semantic_cache extension works out of the box without special
configuration, but for optimal performance with large caches use the
following settings:

```ini
# Recommended for production with large caches
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
work_mem = 256MB                        # For vector operations
maintenance_work_mem = 1GB              # For index creation

# Enable query timing (optional, for monitoring)
track_io_timing = on
```

Restart PostgreSQL after making configuration changes:

```bash
# Systemd
sudo systemctl restart postgresql

# Or using pg_ctl
pg_ctl restart -D /var/lib/postgresql/data
```

## Testing the Installation

Validate your installation by running the test suite or manual tests. You can
use the following command to run the included test suite:

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

You can remove pg_semantic_cache from your database and system when it
is no longer needed. Use the following command:

```sql
DROP EXTENSION IF EXISTS pg_semantic_cache CASCADE;
```

Then, clean up extension files from PostgreSQL directories:

```bash
cd pg_semantic_cache
sudo make uninstall
```

This removes the following files:

- The shared library file with the .so extension.
- The control file.
- The SQL installation files.

