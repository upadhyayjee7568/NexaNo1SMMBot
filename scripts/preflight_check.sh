#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found"
  exit 1
fi

required=(
  APP_NAME
  PROJECT_NAME
  DATABASE_URL
  PAYMENT_GATEWAY
  CASHFREE_WEBHOOK_SECRET
  PROVIDER_1_BASE_URL
  PROVIDER_1_API_KEY
  TELEGRAM_BOT_TOKEN
)

missing=0
for k in "${required[@]}"; do
  if ! grep -Eq "^${k}=" "$ENV_FILE"; then
    echo "MISSING: $k"
    missing=1
  fi
done

if grep -Eq '^PAYMENT_GATEWAY="?cashfree"?$' "$ENV_FILE"; then
  :
else
  echo "ERROR: PAYMENT_GATEWAY must be cashfree"
  missing=1
fi

if grep -Eq 'REPLACE_WITH_|CHANGE_ME|YOUR_' "$ENV_FILE"; then
  echo "ERROR: Placeholder values detected in $ENV_FILE"
  missing=1
fi

if [ "$missing" -ne 0 ]; then
  echo "Preflight failed"
  exit 1
fi

echo "Preflight passed"
