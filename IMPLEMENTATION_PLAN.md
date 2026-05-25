# Nexa SMM Panel - Implementation Plan (Ready to Deploy Base)

## Completed in this repository
- FastAPI service with health, config summary, platform catalog, and order placement endpoint.
- Multi-provider order engine skeleton with automatic fallback.
- Cashfree-only payment policy through env config.
- Docker + docker-compose + deploy script.
- Secure env template and security hardening checklist.

## API endpoints
- `GET /api/health`
- `GET /api/config/summary`
- `GET /api/services/platforms`
- `POST /api/orders/place`

## Next production steps
1. Add PostgreSQL models + Alembic migrations (users, wallet_ledger, orders, tickets).
2. Add Telegram bot worker and webhook handlers.
3. Add Cashfree webhook signature verification and wallet credit logic.
4. Add provider service sync cron and dynamic rate cache.
5. Add admin RBAC + 2FA enforcement.
