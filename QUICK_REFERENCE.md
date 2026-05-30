# Nexa SMM Panel - Quick Reference Guide

## Admin Access

### Dashboard URLs
- **Admin Home**: `/admin`
- **Users**: `/admin/users`
- **Payments & UPI**: `/admin/payments`
- **Services**: `/admin/services`
- **Tickets**: `/admin/tickets`
- **System Health**: `/health/dashboard`
- **Logout**: `/web/logout`

## Customer Access

### Panel URLs
- **Home**: `/app`
- **Wallet**: `/app/wallet`
- **My Orders**: `/app/orders` (auto-loaded on home)
- **Logout**: `/web/logout`

## API Endpoints

### Health & Status
- `GET /api/health` - Quick status check
- `GET /api/health/detailed` - Full component report (JSON)
- `GET /healthz` - Kubernetes-style health check

### Payment & Orders
- `POST /api/payments/add-money` - Initiate payment
- `GET /api/orders/{order_id}` - Get order details
- `POST /api/orders/cancel` - Cancel order

### Webhooks
- `POST /api/payments/cashfree/webhook` - Cashfree payment callback
- `POST /api/webhook/telegram` - Telegram bot updates

## Key Features

### Auto-Failover
- Cashfree → UPI QR code automatic fallback if payment gateway fails
- UPI QR is generated with app-level encryption
- Admin approves/rejects UPI payments from dashboard

### Health Monitoring
- Checks every 5 minutes
- Auto-restarts after 3 consecutive failures
- Sends Telegram alerts on critical failures
- Monitored components:
  - Database (PostgreSQL)
  - Telegram bot webhook
  - Main API
  - Cashfree payment gateway
  - UPI fallback provider

### Admin Dashboard Features
- Real-time statistics (Users, Orders, Payments, Pending UPI)
- User management with role badges
- Payment transaction history
- UPI request approve/reject interface
- Service catalog browser
- Support ticket manager
- Coupon creation
- CSV export for reports

### Customer Dashboard Features
- Wallet balance display
- Add money form
- Coupon application
- Recent orders table (20 latest)
- Order status tracking
- Direct Telegram support link

## User Roles

- **Admin**: Full access to all management pages
- **Moderator**: Limited access (TBD)
- **User**: Customer portal only

## Database

### Connection
- **Type**: PostgreSQL (Neon)
- **Pool**: SQLAlchemy with connection pooling
- **Migrations**: Alembic with 9 migrations

### Key Tables
- `users` - User accounts
- `orders` - Customer orders
- `payment_transactions` - Payment history
- `upi_topup` - UPI payment requests
- `wallet_ledger` - Wallet transaction log
- `service_catalog` - Available services
- `tickets` - Support tickets
- `coupons` - Discount codes

## Telegram Bot

### Bot Commands
- `/start` - Initialize bot
- `/wallet` - Check balance
- `/orders` - View orders
- `/daily` - Claim daily reward
- `/support` - Open support ticket

### Webhook Mode
- Receives updates via POST to `/api/webhook/telegram`
- Configured for Vercel deployment
- No polling required

## Deployment

### Vercel
```bash
git push origin smm-panel-build
vercel deploy
```

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection (from Neon)
- `TELEGRAM_BOT_TOKEN` - Bot API token
- `TELEGRAM_ADMIN_ID` - Admin user ID for alerts
- `CASHFREE_CLIENT_ID` - Payment gateway ID
- `CASHFREE_CLIENT_SECRET` - Payment gateway secret

### Health Check
```bash
curl https://your-app.vercel.app/healthz
curl https://your-app.vercel.app/api/health/detailed
```

## Development

### Running Locally
```bash
# Setup venv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
PYTHONPATH=. alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
pytest -xvs
```

### File Structure
```
app/
├── api/              # API routes
├── bot/              # Telegram bot
├── core/             # Settings, models, RBAC
├── db/               # Database models, session
├── services/         # Business logic
│   ├── health_monitor.py  # NEW: Health monitoring
│   ├── cashfree.py        # Payment gateway
│   ├── upi_fallback.py    # UPI auto-fallback
│   ├── order_engine.py    # Order processing
│   └── ...
├── web/              # Web UI
│   ├── routes.py     # Web endpoints
│   └── templates/    # Jinja2 templates
│       ├── admin.html           # Admin dashboard
│       ├── customer.html        # Customer panel
│       ├── health_dashboard.html # NEW: Health UI
│       └── ...
└── main.py           # FastAPI app
```

## Monitoring

### View Health Status
1. Navigate to `/health/dashboard` (admin only)
2. Check component status
3. View last check time
4. Click API endpoints for JSON data

### Logs
- Check `[HEALTH]` prefixed logs for monitoring events
- Check `[STARTUP]` logs for initialization
- Check Telegram for admin alerts

## Troubleshooting

### Database Connection
- Check `DATABASE_URL` in environment
- Verify Neon password is correct
- Check IP allowlist in Neon dashboard

### Bot Not Responding
- Verify `TELEGRAM_BOT_TOKEN` is set
- Check webhook URL in Telegram settings
- Check `/api/health` for bot status
- View `/health/dashboard` for detailed status

### Payments Not Working
- Check `/admin/payments` for transaction history
- View `/health/dashboard` for Cashfree status
- UPI fallback should activate automatically
- Check admin alerts for failures

### No Admin Alerts
- Verify `TELEGRAM_ADMIN_ID` is set
- Check bot token is correct
- Verify health monitoring is running
- Check app logs for alert send errors
