from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.models import CreateOrderRequest
from app.core.rbac import get_actor, require_role
from app.core.settings import settings
from app.db.models import Coupon, Order, PaymentTransaction, Referral, ServiceCatalog, UpiTopup, User, WalletLedger
from app.db.session import SessionLocal
from app.services import cashfree as cashfree_svc
from app.services import upi_fallback
from app.services.cashfree_webhook import extract_event_id, is_success_event, safe_dump, verify_cashfree_signature
from app.services.finance import fetch_finance_daily_report, post_double_entry
from app.services.growth import apply_coupon, credit_daily_reward, register_referral, vip_discount_percent
from app.services.order_engine import place_order
from app.services.order_lifecycle import refresh_order_status, request_cancel, request_refill
from app.services.platforms import platform_catalog
from app.services.pricing import compute_final_amount, resolve_category
from app.services.tickets import create_ticket, list_ticket_messages, list_tickets_by_telegram, reply_ticket
from app.services.wallet import add_ledger_entry, wallet_balance
from app.services.health_monitor import get_health_status

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('/health')
def health() -> dict:
    return {'status': 'ok', 'service': settings.app_name, 'env': settings.environment}


@router.get('/health/detailed')
def health_detailed() -> dict:
    """Get detailed system health status with component checks."""
    return get_health_status()


@router.get('/config/summary')
def config_summary() -> dict:
    return {
        'project_name': settings.project_name,
        'bot_username': settings.telegram_bot_username,
        'payment_gateway': settings.payment_gateway,
        'timezone': settings.timezone,
    }


@router.get('/services/platforms')
def services_platforms() -> dict:
    platforms = platform_catalog()
    return {'platforms': platforms, 'count': len(platforms)}


@router.post('/orders/place')
async def orders_place(payload: CreateOrderRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == payload.user_id).first()
    if not user:
        user = User(telegram_id=payload.user_id)
        db.add(user)
        db.flush()

    service = db.query(ServiceCatalog).filter(ServiceCatalog.id == payload.service_id, ServiceCatalog.enabled.is_(True)).first()
    if not service:
        raise HTTPException(status_code=404, detail='Service not found')

    category = resolve_category(service.platform, service.service_name)
    vip_percent = Decimal(str(vip_discount_percent(sum([Decimal(str(x[0])) for x in db.query(Order.charge_amount).filter(Order.user_id == user.id).all()], Decimal('0')))))
    coupon_percent = Decimal('0')
    coupon_code = request.headers.get('X-Coupon-Code')
    if coupon_code:
        c = db.query(Coupon).filter(Coupon.code == coupon_code.upper(), Coupon.active.is_(True)).first()
        if c and (c.max_uses is None or c.used_count < c.max_uses):
            coupon_percent = Decimal(str(c.discount_percent))
            c.used_count += 1
            db.flush()

    final_amount = compute_final_amount(
        base_rate=Decimal(str(service.base_rate)),
        quantity=payload.quantity,
        category=category,
        vip_discount_percent=vip_percent,
        coupon_discount_percent=coupon_percent,
        user_bear_fee_percent=Decimal('2'),
    )

    if wallet_balance(db, user.id) < final_amount:
        raise HTTPException(status_code=400, detail='Insufficient wallet balance')

    result = await place_order(payload.service_id, str(payload.link), payload.quantity, base_rate=float(service.base_rate), category=category)
    if result.get('status') == 'created':
        order = Order(
            client_order_id=result['order_id'],
            user_id=user.id,
            provider_name=result['provider'],
            provider_order_id=result.get('provider_order_id'),
            service_id=payload.service_id,
            link=str(payload.link),
            quantity=payload.quantity,
            charge_amount=final_amount,
            status='created',
        )
        db.add(order)
        add_ledger_entry(db, user.id, 'debit', final_amount, reference_id=result['order_id'])
        post_double_entry(db, entry_ref=f"order:{result['order_id']}", description='Order debit', debit_account='wallet_user', credit_account='revenue_hold', amount=final_amount, user_id=user.id)
        db.commit()
    return result


@router.post('/telegram/webhook')
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    # Telegram echoes the secret token configured via setWebhook; reject anything else.
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail='Invalid webhook secret')
    update = await request.json()
    from app.bot.webhook import handle_update

    try:
        await handle_update(update, db)
    except Exception:  # noqa: BLE001
        # Always return 200 so Telegram does not spam-retry a poison update.
        import logging

        logging.getLogger('nexa.bot').exception('Failed to handle update')
    return {'ok': True}


@router.post('/telegram/set-webhook')
async def telegram_set_webhook(request: Request) -> dict:
    """Admin helper to register the Telegram webhook. Guarded by the webhook secret."""
    body = await request.json()
    if not settings.telegram_webhook_secret or body.get('secret') != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail='Invalid secret')
    if not settings.public_base_url:
        raise HTTPException(status_code=400, detail='PUBLIC_BASE_URL not configured')
    import httpx

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
    webhook_url = f"{settings.public_base_url.rstrip('/')}/api/telegram/webhook"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            json={
                'url': webhook_url,
                'secret_token': settings.telegram_webhook_secret,
                'allowed_updates': ['message', 'edited_message', 'callback_query'],
                'drop_pending_updates': True,
            },
        )
    return {'webhook_url': webhook_url, 'telegram_response': resp.json()}


@router.get('/wallet/{telegram_id}')
def get_wallet(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'balance': '0.00', 'currency': 'INR'}
    return {'telegram_id': telegram_id, 'balance': str(wallet_balance(db, user.id)), 'currency': 'INR'}


@router.post('/payments/add-money/initiate')
async def add_money_initiate(request: Request, db: Session = Depends(get_db)) -> dict:
    """Start a wallet top-up. Tries Cashfree first; on any failure falls back to UPI QR."""
    body = await request.json()
    telegram_id = int(body.get('telegram_id') or 0)
    amount = Decimal(str(body.get('amount') or 0))
    phone = body.get('phone')
    if telegram_id <= 0:
        raise HTTPException(status_code=400, detail='telegram_id required')
    if amount < Decimal(str(settings.min_add_money_inr)):
        raise HTTPException(status_code=400, detail=f'Minimum add money is INR {settings.min_add_money_inr}')
    if amount > Decimal(str(settings.max_add_money_inr)):
        raise HTTPException(status_code=400, detail=f'Maximum add money is INR {settings.max_add_money_inr}')

    # 1) Try Cashfree
    if cashfree_svc.is_configured():
        try:
            link = await cashfree_svc.create_payment_link(telegram_id, amount, phone=phone)
            return {'method': 'cashfree', 'amount': str(amount), **link}
        except cashfree_svc.CashfreeError:
            pass  # fall through to UPI

    # 2) UPI fallback
    if not settings.upi_fallback_enabled or not settings.admin_upi_id:
        raise HTTPException(status_code=503, detail='No payment method available right now')
    try:
        topup, uri, qr = upi_fallback.create_upi_topup(db, telegram_id, amount)
    except upi_fallback.UpiError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        'method': 'upi',
        'amount': str(amount),
        'reference': topup.reference,
        'upi_id': topup.upi_id,
        'upi_uri': uri,
        'qr_data_uri': qr,
        'note': 'Pay using any UPI app, then submit your 12-digit UTR/reference number to credit your wallet.',
    }


@router.post('/payments/upi/submit-utr')
async def upi_submit_utr(request: Request, db: Session = Depends(get_db)) -> dict:
    body = await request.json()
    reference = str(body.get('reference') or '').strip()
    utr = str(body.get('utr') or '').strip()
    if not reference:
        raise HTTPException(status_code=400, detail='reference required')
    try:
        topup, status = upi_fallback.submit_utr(db, reference, utr)
    except upi_fallback.UpiError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if status == 'not_found':
        raise HTTPException(status_code=404, detail='Top-up reference not found')
    return {
        'ok': status in {'credited', 'pending_review'},
        'status': status,
        'reference': reference,
        'amount': str(topup.amount) if topup else None,
    }


@router.get('/payments/upi/{reference}')
def upi_status(reference: str, db: Session = Depends(get_db)) -> dict:
    topup = db.query(UpiTopup).filter(UpiTopup.reference == reference).first()
    if not topup:
        raise HTTPException(status_code=404, detail='Not found')
    return {'reference': reference, 'status': topup.status, 'amount': str(topup.amount), 'utr': topup.utr}


@router.post('/payments/cashfree/webhook')
async def cashfree_webhook(request: Request, x_cashfree_signature: str | None = Header(default=None), db: Session = Depends(get_db)) -> dict:
    if settings.payment_gateway.lower() != 'cashfree':
        raise HTTPException(status_code=400, detail='Cashfree gateway is disabled')
    raw = await request.body()
    verify_cashfree_signature(raw, x_cashfree_signature)
    payload = await request.json()
    event_id = extract_event_id(payload)

    if db.query(PaymentTransaction).filter(PaymentTransaction.gateway == 'cashfree', PaymentTransaction.gateway_event_id == event_id).first():
        return {'ok': True, 'skipped': 'duplicate_event', 'event_id': event_id}

    telegram_id = int(payload.get('customer_details', {}).get('customer_id', 0) or 0)
    amount = Decimal(str(payload.get('order_amount', '0')))
    if amount < Decimal(str(settings.min_add_money_inr)):
        db.commit()
        return {'ok': True, 'skipped': 'below_min_add_money', 'event_id': event_id}
    db.add(PaymentTransaction(gateway='cashfree', gateway_event_id=event_id, order_id=str(payload.get('order_id', '')) or None, telegram_id=telegram_id or None, amount=amount, currency='INR', status=str(payload.get('order_status', 'received')).lower(), raw_payload=safe_dump(payload)))

    if is_success_event(payload.get('order_status')) and telegram_id and amount > 0:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            db.flush()
        ref = f"cashfree:{event_id}"
        if not db.query(WalletLedger).filter(WalletLedger.user_id == user.id, WalletLedger.reference_id == ref, WalletLedger.entry_type == 'credit').first():
            add_ledger_entry(db, user.id, 'credit', amount, reference_id=ref)
            post_double_entry(db, entry_ref=ref, description='Wallet topup via Cashfree', debit_account='cashfree_clearing', credit_account='wallet_user', amount=amount, user_id=user.id)
        referral = db.query(Referral).filter(Referral.referred_user_id == user.id).first()
        if referral:
            reward = (amount * Decimal(str(referral.reward_percent)) / Decimal('100')).quantize(Decimal('0.01'))
            add_ledger_entry(db, referral.referrer_user_id, 'credit', reward, reference_id=f'referral:{event_id}', note='Referral reward')

    db.commit()
    return {'ok': True, 'event_id': event_id}
