#!/bin/bash
set -e

echo "Database connection settings:"
echo "Host: $POSTGRES_HOST"
echo "User: $POSTGRES_USER"
echo "Database: $POSTGRES_DB"
echo "Password: ${POSTGRES_PASSWORD:0:1}****"

echo "Waiting for PostgreSQL to start..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT"  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\l'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing migrations"
echo "Current directory: $(pwd)"
echo "Listing directory contents:"
ls -la
echo "Listing alembic directory:"
ls -la alembic/

echo "Running migrations..."
# Добавим вывод текущей ревизии для отладки
alembic current
echo "Current revision listed above"
echo "Applying migrations..."
alembic upgrade head

echo "Migrations completed successfully"