from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.models import CreateOrderRequest
from app.core.rbac import get_actor, require_role
from app.core.settings import settings
from app.db.models import Coupon, Order, PaymentTransaction, Referral, ServiceCatalog, User, WalletLedger
from app.db.session import SessionLocal
from app.services.cashfree_webhook import extract_event_id, is_success_event, safe_dump, verify_cashfree_signature
from app.services.finance import fetch_finance_daily_report, post_double_entry
from app.services.growth import apply_coupon, credit_daily_reward, register_referral, vip_discount_percent
from app.services.order_engine import place_order
from app.services.order_lifecycle import refresh_order_status, request_cancel, request_refill
from app.services.platforms import platform_catalog
from app.services.pricing import compute_final_amount, resolve_category
from app.services.tickets import create_ticket, list_ticket_messages, list_tickets_by_telegram, reply_ticket
from app.services.wallet import add_ledger_entry, wallet_balance

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


@router.get('/wallet/{telegram_id}')
def get_wallet(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'balance': '0.00', 'currency': 'INR'}
    return {'telegram_id': telegram_id, 'balance': str(wallet_balance(db, user.id)), 'currency': 'INR'}


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
