#!/bin/bash
set -e

PGDATA="/var/lib/postgresql/data"
PGBIN="/usr/lib/postgresql/18/bin"

init_database() {
    echo "Initializing PostgreSQL database..."
    $PGBIN/initdb -D "$PGDATA" --encoding=UTF8 --locale=C.UTF-8

    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"

    echo "Database initialized successfully"
}

start_postgres_temp() {
    echo "Starting PostgreSQL temporarily for setup..."
    $PGBIN/pg_ctl -D "$PGDATA" -o "-c listen_addresses=''" -w start
}

stop_postgres_temp() {
    echo "Stopping temporary PostgreSQL..."
    $PGBIN/pg_ctl -D "$PGDATA" -m fast -w stop
}

run_setup() {
    echo "Setting postgres password..."
    $PGBIN/psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"

    echo "Running setup.sql..."
    $PGBIN/psql -U postgres -d postgres -f /tmp/setup.sql
    echo "Setup completed successfully"
}

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "==================================================================="
    echo "First run detected - initializing fresh database..."
    echo "==================================================================="

    init_database
    start_postgres_temp
    run_setup
    stop_postgres_temp

    echo "==================================================================="
    echo "Initialization complete - starting PostgreSQL normally..."
    echo "==================================================================="
else
    echo "==================================================================="
    echo "Existing database found - starting PostgreSQL..."
    echo "==================================================================="
fi

exec $PGBIN/postgres -D "$PGDATA"
