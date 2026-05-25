#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

curl -fsS "$BASE_URL/api/health"
echo
curl -fsS "$BASE_URL/api/config/summary"
echo
curl -fsS "$BASE_URL/api/services/platforms"
echo
