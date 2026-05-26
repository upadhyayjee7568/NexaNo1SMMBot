#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

if [ ! -f .env.production ]; then
  echo "ERROR: .env.production not found. Create it from .env.production.example first."
  exit 1
fi

echo "[1/6] Running preflight checks..."
./scripts/preflight_check.sh .env.production

echo "[2/6] Building containers..."
docker compose build

echo "[3/6] Starting dependencies (postgres, redis)..."
docker compose up -d postgres redis

echo "[4/6] Running DB migrations..."
docker compose run --rm api alembic upgrade head

echo "[5/6] Starting application service..."
docker compose up -d api

echo "[6/6] Running health checks..."
./scripts/check_health.sh "$BASE_URL"

echo "Deployment complete"
docker compose ps
