# NexaNo1SMMBot

Production-ready starter backend for **Nexa SMM Panel** with secure config template and Docker deployment.

## Included
- FastAPI backend scaffold (`app/`) with health, config, order placement, wallet, and Cashfree webhook endpoints.
- Launch-ready multi-platform catalog (Instagram, Telegram, YouTube, Facebook + more).
- Cashfree-only payment configuration approach.
- SQLAlchemy models + Alembic migration for users, orders, and wallet ledger.
- FastAPI backend scaffold (`app/`) with health + config + platform services endpoints.
- Launch-ready multi-platform catalog (Instagram, Telegram, YouTube, Facebook + more).
- Cashfree-only payment configuration approach.
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
3. Run deployment:
   ```bash
   ./scripts/deploy.sh
   ```
4. Verify:
   - `GET /api/health`
   - `GET /api/config/summary`
   - `GET /api/services/platforms`

## Services Platforms (launch)
- Instagram
- YouTube
- Telegram
- Facebook
- X
- TikTok
- LinkedIn
- Spotify
- Threads
- Snapchat
- Pinterest
- Website Traffic

## Notes
- Never commit real secrets.
- Rotate any token/key shared in public channels.
Configuration baseline for **Nexa Media Solution / Nexa SMM Panel**.

## Files
- `PROJECT_SETUP.md` — business + product requirements snapshot.
- `config.nexa.example.yaml` — implementation-ready config template (replace placeholder secrets before production use).
