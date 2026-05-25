# Security + Deployment Secret Handling

This repository intentionally stores only **templates** and **placeholder secrets**.

## 1) Do NOT commit real secrets
Never commit these to GitHub:
- Telegram bot token
- Cashfree secret key
- Provider API keys
- JWT/app encryption keys

Use `.env.production` on server only. `.gitignore` is configured to block `.env*` files except examples.

## 2) Required secure flow
1. Copy `.env.production.example` to `.env.production` on your VPS.
2. Replace every `REPLACE_WITH_...` value with real secrets.
3. Restrict file permissions:
   ```bash
   chmod 600 .env.production
   ```
4. Inject env vars into your runtime (Docker Compose / systemd / platform secrets manager).

## 3) Immediate key rotation recommendation
Because real secrets were shared in chat, rotate all of these before go-live:
- Telegram bot token
- Cashfree secret key
- Provider 1 API key
- Provider 2 API key

## 4) Payment gateway policy
This setup supports **Cashfree only** for production as requested.

## 5) Webhook validation
- Generate a separate webhook secret in Cashfree dashboard.
- Verify signature on each webhook before wallet credit.
- Reject unsigned/invalid events.
