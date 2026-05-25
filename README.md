# NexaNo1SMMBot

Production-ready starter backend for **Nexa SMM Panel** with secure config template and Docker deployment.

## Included
- FastAPI backend scaffold (`app/`) with health, config, order placement, wallet, and Cashfree webhook endpoints.
- Launch-ready multi-platform catalog (Instagram, Telegram, YouTube, Facebook + more).
- Cashfree-only payment configuration approach.
- SQLAlchemy models + Alembic migration for users, orders, and wallet ledger.
- Production env template (`.env.production.example`) and security guide (`SECURITY_SETUP.md`).
- Dockerized deployment (`Dockerfile`, `docker-compose.yml`, `scripts/deploy.sh`).

## Quick Deploy (VPS)
1. Copy env template:
   ```bash
   cp .env.production.example .env.production
   ```
2. Set real secrets in `.env.production`.
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Run deployment:
   ```bash
   ./scripts/deploy.sh
   ```

## Test
```bash
python -m pytest -q
```


## Ops Scripts
- `scripts/run_migrations.sh` — apply DB migrations.
- `scripts/run_api.sh` — start API service.
- `scripts/sync_services.py` — pull provider services snapshot.
- `scripts/order_status_sync.py` — sync live order statuses from providers.
- `scripts/bootstrap_admin.py` — create bootstrap super admin user.

- `scripts/refund_failed_orders.py` — auto-refund failed/cancelled orders to wallet (idempotent).

- `scripts/run_all_crons.sh` — run all maintenance jobs sequentially.
- `scripts/check_health.sh` — quick API health/config/platform smoke check.

- `scripts/run_bot.sh` — run Telegram bot polling runtime (/start, /help, /support, force-join check).


## RBAC Admin APIs
- `POST /api/admin/users/role` (superadmin required via `X-Telegram-Id`)
- `POST /api/admin/users/ban` (support+ required via `X-Telegram-Id`)
- `GET /api/admin/orders` (support+ required via `X-Telegram-Id`)

- `GET /api/services/catalog` — DB-backed service catalog (optional `platform` filter).


## Order Lifecycle APIs
- `GET /api/orders/track/{client_order_id}` — live provider status refresh + return local status.
- `POST /api/orders/refill/{client_order_id}` — submit refill request to provider.
- `POST /api/orders/cancel/{client_order_id}` — submit cancel request to provider.
- `POST /api/admin/orders/retry/{client_order_id}` — admin retry routing for failed orders.

- `GET /api/admin/finance/report/daily` — export-ready daily finance aggregates (wallet ledger view).


## Ticket APIs
- `POST /api/tickets` — create ticket.
- `GET /api/tickets/{telegram_id}` — list user tickets.
- `GET /api/tickets/messages/{ticket_ref}` — list messages (owner/support).
- `POST /api/admin/tickets/reply/{ticket_ref}` — support/admin reply and optional close.
