#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env.production ]; then
  echo "ERROR: .env.production not found. Create it from .env.production.example first."
  exit 1
fi

echo "[1/3] Building containers..."
docker compose build

echo "[2/3] Starting services..."
docker compose up -d

echo "[3/3] Deployment complete."
docker compose ps
