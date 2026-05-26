#!/usr/bin/env bash
set -euo pipefail

# Run sequential maintenance jobs
python scripts/sync_services.py || true
python scripts/order_status_sync.py || true
python scripts/refund_failed_orders.py || true

echo "All cron jobs executed"
