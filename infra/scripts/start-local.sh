#!/bin/bash
set -e

echo "=== COGNET LDI Engine — Local Development Startup ==="

# הפעלת תשתית
echo "→ Starting PostgreSQL and Redis..."
cd "$(dirname "$0")/../docker"
docker-compose up -d postgres redis

echo "→ Waiting for services to be ready..."
sleep 5

# הרצת מיגרציות
echo "→ Running database migrations..."
cd "$(dirname "$0")/../../"
export PYTHONPATH="$(pwd)/apps/api:$(pwd)/services:$(pwd)"
cd infra
alembic upgrade head

echo "→ Starting API server..."
cd ../apps/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo "✓ COGNET LDI Engine is running at http://localhost:8000"
