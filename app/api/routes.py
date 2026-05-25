from decimal import Decimal
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.models import CreateOrderRequest
from app.core.settings import settings
from app.db.session import SessionLocal
from app.db.models import Order, User
from app.services.order_engine import place_order
from app.services.platforms import platform_catalog
from app.services.wallet import wallet_balance, add_ledger_entry
from app.services.cashfree_webhook import verify_cashfree_signature, is_success_event

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
    return {'platforms': platform_catalog(), 'count': len(platform_catalog())}


@router.post('/orders/place')
async def orders_place(payload: CreateOrderRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == payload.user_id).first()
    if not user:
        user = User(telegram_id=payload.user_id)
        db.add(user)
        db.flush()

    balance = wallet_balance(db, user.id)
    estimated_charge = Decimal(str(round(payload.quantity * 1.25, 2)))
    if balance < estimated_charge:
        raise HTTPException(status_code=400, detail='Insufficient wallet balance')

    result = await place_order(payload.service_id, str(payload.link), payload.quantity, base_rate=1.0)
    if result.get('status') == 'created':
        order = Order(
            client_order_id=result['order_id'],
            user_id=user.id,
            provider_name=result['provider'],
            provider_order_id=result.get('provider_order_id'),
            service_id=payload.service_id,
            link=str(payload.link),
            quantity=payload.quantity,
            charge_amount=Decimal(str(result['charged_amount'])),
            status='created',
        )
        db.add(order)
        add_ledger_entry(db, user.id, 'debit', Decimal(str(result['charged_amount'])), reference_id=result['order_id'])
        db.commit()
    return result


@router.get('/wallet/{telegram_id}')
def get_wallet(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'balance': '0.00', 'currency': 'INR'}
    balance = wallet_balance(db, user.id)
    return {'telegram_id': telegram_id, 'balance': str(balance), 'currency': 'INR'}


@router.post('/payments/cashfree/webhook')
async def cashfree_webhook(request: Request, x_cashfree_signature: str | None = Header(default=None), db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    verify_cashfree_signature(raw, x_cashfree_signature)
    payload = await request.json()

    if not is_success_event(payload.get('order_status')):
        return {'ok': True, 'skipped': 'non_success_status'}

    telegram_id = int(payload.get('customer_details', {}).get('customer_id', 0) or 0)
    amount = Decimal(str(payload.get('order_amount', '0')))
    if telegram_id and amount > 0:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            db.add(user)
            db.flush()

        ref = str(payload.get('order_id', 'cashfree'))
        add_ledger_entry(db, user.id, 'credit', amount, reference_id=ref)
        db.commit()

    return {'ok': True}
