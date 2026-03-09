# Development Resources

Developer contributions are welcome! This extension is built with standard PostgreSQL C APIs.

To create a development installation:

1. Fork the repository.
2. Create a feature branch for your changes.
3. Make your changes to the codebase.
4. Run the test suite with `make installcheck`.
5. Submit a pull request with your changes.

Code guidelines:

- Follow the existing code style throughout the project.
- Add tests for any new features you implement.
- Update the documentation to reflect your changes.
- Ensure your changes are compatible with PostgreSQL versions 14 through 18.

---

## Building From Source

The extension uses the standard PostgreSQL PGXS build system for compilation and installation.


```bash
# Standard build
make clean && make
sudo make install

# Run tests
make installcheck

# Development build with debug symbols
make CFLAGS="-g -O0" clean all

# View build configuration
make info
```

## Performing a Multi-Version PostgreSQL Build

The extension supports building for multiple PostgreSQL versions in sequence.

Build for multiple PostgreSQL versions simultaneously:

```bash
for PG in 14 15 16 17 18; do
    echo "Building for PostgreSQL $PG..."
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```
