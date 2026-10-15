#!/bin/bash
set -e

# Extract host and port from Airflow connection string (assumes postgres://)
POSTGRES_HOST=$(echo "$AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" | sed -E 's|^.+://[^@]+@([^:/]+).*|\1|')
POSTGRES_PORT=$(echo "$AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" | sed -E 's|^.+://[^@]+@[^:/]+:([0-9]+).*|\1|')
POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Wait for PostgreSQL to be ready
echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"; do
    sleep 1
done
echo "Postgres is ready."

echo "Running Airflow DB migration..."
airflow db migrate

# Start Airflow services
echo "Starting Airflow scheduler and API server..."
airflow scheduler &

exec airflow webserver