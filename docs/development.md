# Development Resources

We welcome developer contributions to the pg_semantic_cache extension. The
extension is built with standard PostgreSQL C APIs and follows the
PostgreSQL extension development model.

## Contributing to the Project

To create a development installation and contribute to the project, follow
these steps in order:

1. Fork the repository on GitHub.
2. Create a feature branch for your changes.
3. Make your changes to the codebase.
4. Run the test suite with `make installcheck`.
5. Submit a pull request with your changes.

The following guidelines apply to all code contributions:

- Follow the existing code style throughout the project.
- Add tests for any new features you implement.
- Update the documentation to reflect your changes.
- Ensure your changes are compatible with PostgreSQL 14 through 18.

## Building From Source

The extension uses the standard PostgreSQL PGXS build system for
compilation and installation. The PGXS system provides a consistent build
environment across all PostgreSQL versions.

In the following example, the `make` commands build and install the
extension from source:

```bash
make clean && make
sudo make install

make installcheck

make CFLAGS="-g -O0" clean all

make info
```

The first command builds the extension. The second command runs the test
suite. The third command creates a development build with debug symbols.
The fourth command displays the build configuration.

## Building for Multiple PostgreSQL Versions

The extension supports building for multiple PostgreSQL versions in
sequence. This approach is useful for package maintainers and multi-version
testing environments.

In the following example, the `for` loop builds the extension for
PostgreSQL versions 14 through 18:

```bash
for PG in 14 15 16 17 18; do
    echo "Building for PostgreSQL $PG..."
    PG_CONFIG=/usr/pgsql-${PG}/bin/pg_config make clean install
done
```
