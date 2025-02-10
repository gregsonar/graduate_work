#!/bin/bash
set -e

echo "Database connection settings:"
echo "Host: $SUB_POSTGRES_HOST"
echo "User: $SUB_POSTGRES_USER"
echo "Database: $SUB_POSTGRES_DB"
echo "Password: ${SUB_POSTGRES_PASSWORD:0:1}****"

echo "Waiting for PostgreSQL to start..."
until PGPASSWORD=$SUB_POSTGRES_PASSWORD psql -h "$SUB_POSTGRES_HOST" -p "$SUB_POSTGRES_PORT"  -U "$SUB_POSTGRES_USER" -d "$SUB_POSTGRES_DB" -c '\l'; do
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
alembic revision --autogenerate
echo "Applying migrations..."
alembic upgrade head

echo "Migrations completed successfully"