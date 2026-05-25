from decimal import Decimal
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from app.core.models import CreateOrderRequest
from app.core.settings import settings
from app.core.rbac import get_actor, require_role
from app.db.session import SessionLocal
from app.db.models import Order, User, WalletLedger, ServiceCatalog, PaymentTransaction, Ticket, TicketMessage
from app.services.order_engine import place_order
from app.services.order_lifecycle import refresh_order_status, request_refill, request_cancel
from app.services.tickets import create_ticket
from app.db.models import Order, User, WalletLedger, ServiceCatalog, PaymentTransaction
from app.db.models import Order, User, WalletLedger, ServiceCatalog
from app.services.order_engine import place_order
from app.services.order_lifecycle import refresh_order_status, request_refill, request_cancel
from app.services.platforms import platform_catalog
from app.services.wallet import wallet_balance, add_ledger_entry
from app.services.finance import post_double_entry, fetch_finance_daily_report
from app.services.cashfree_webhook import verify_cashfree_signature, is_success_event, extract_event_id, safe_dump
from app.services.cashfree_webhook import verify_cashfree_signature, is_success_event, extract_event_id, safe_dump
from app.services.cashfree_webhook import verify_cashfree_signature, is_success_event
from app.db.models import Order, User, WalletLedger
from app.db.session import SessionLocal
from app.db.models import Order, User, WalletLedger
from app.db.models import Order, User
from app.services.order_engine import place_order
from app.services.platforms import platform_catalog
from app.services.wallet import wallet_balance, add_ledger_entry
from app.services.cashfree_webhook import verify_cashfree_signature, is_success_event
from app.services.cashfree_webhook import verify_cashfree_signature
from fastapi import APIRouter

from app.core.models import CreateOrderRequest
from app.core.settings import settings
from app.services.order_engine import place_order
from app.core.settings import settings
from app.services.platforms import platform_catalog

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
    result = await place_order(payload.service_id, payload.link, payload.quantity, base_rate=1.0)
    if result.get('status') == 'created':
        order = Order(
            client_order_id=result['order_id'],
            user_id=user.id,
            provider_name=result['provider'],
            provider_order_id=result.get('provider_order_id'),
            service_id=payload.service_id,
            link=str(payload.link),
            link=payload.link,
            quantity=payload.quantity,
            charge_amount=Decimal(str(result['charged_amount'])),
            status='created',
        )
        db.add(order)
        add_ledger_entry(db, user.id, 'debit', Decimal(str(result['charged_amount'])), reference_id=result['order_id'])
        post_double_entry(db, entry_ref=f"order:{result['order_id']}", description='Order debit', debit_account='wallet_user', credit_account='revenue_hold', amount=Decimal(str(result['charged_amount'])), user_id=user.id)
        db.commit()
    return result


@router.get('/orders/{telegram_id}')
def order_history(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'orders': [], 'count': 0}

    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .limit(100)
        .all()
    )
    data = [
        {
            'client_order_id': o.client_order_id,
            'provider_name': o.provider_name,
            'provider_order_id': o.provider_order_id,
            'service_id': o.service_id,
            'quantity': o.quantity,
            'charge_amount': str(o.charge_amount),
            'status': o.status,
        }
        for o in orders
    ]
    return {'telegram_id': telegram_id, 'orders': data, 'count': len(data)}


    db.commit()
    return result


@router.get('/wallet/{telegram_id}')
def get_wallet(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'balance': '0.00', 'currency': 'INR'}
    balance = wallet_balance(db, user.id)
    return {'telegram_id': telegram_id, 'balance': str(balance), 'currency': 'INR'}


@router.get('/wallet/{telegram_id}/ledger')
def wallet_ledger(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'telegram_id': telegram_id, 'entries': [], 'count': 0}

    entries = (
        db.query(WalletLedger)
        .filter(WalletLedger.user_id == user.id)
        .order_by(WalletLedger.id.desc())
        .limit(100)
        .all()
    )
    data = [
        {
            'entry_type': e.entry_type,
            'amount': str(e.amount),
            'reference_id': e.reference_id,
            'note': e.note,
            'created_at': e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
    return {'telegram_id': telegram_id, 'entries': data, 'count': len(data)}


@router.post('/payments/cashfree/webhook')
async def cashfree_webhook(request: Request, x_cashfree_signature: str | None = Header(default=None), db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    verify_cashfree_signature(raw, x_cashfree_signature)
    payload = await request.json()

    event_id = extract_event_id(payload)
    existing_txn = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.gateway == 'cashfree', PaymentTransaction.gateway_event_id == event_id)
        .first()
    )
    if existing_txn:
        return {'ok': True, 'skipped': 'duplicate_event', 'event_id': event_id}

    status = str(payload.get('order_status', 'received')).lower()
    telegram_id = int(payload.get('customer_details', {}).get('customer_id', 0) or 0)
    amount = Decimal(str(payload.get('order_amount', '0')))

    txn = PaymentTransaction(
        gateway='cashfree',
        gateway_event_id=event_id,
        order_id=str(payload.get('order_id', '')) or None,
        telegram_id=telegram_id or None,
        amount=amount,
        currency='INR',
        status=status,
        raw_payload=safe_dump(payload),
    )
    db.add(txn)
    db.flush()

    if not is_success_event(payload.get('order_status')):
        db.commit()
        return {'ok': True, 'skipped': 'non_success_status', 'event_id': event_id}

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

        ref = f"cashfree:{event_id}"
        ref = str(payload.get('order_id', 'cashfree'))
        exists = (
            db.query(WalletLedger)
            .filter(WalletLedger.user_id == user.id, WalletLedger.reference_id == ref, WalletLedger.entry_type == 'credit')
            .first()
        )
        if not exists:
            add_ledger_entry(db, user.id, 'credit', amount, reference_id=ref)
            post_double_entry(db, entry_ref=f"cashfree:{event_id}", description='Wallet topup via Cashfree', debit_account='cashfree_clearing', credit_account='wallet_user', amount=amount, user_id=user.id)

    db.commit()
    return {'ok': True, 'event_id': event_id}

    db.commit()
    return {'ok': True, 'event_id': event_id}
        if exists:
            return {'ok': True, 'skipped': 'duplicate_webhook'}

        add_ledger_entry(db, user.id, 'credit', amount, reference_id=ref)
        db.commit()

    return {'ok': True}


@router.post('/admin/users/role')
def set_user_role(
    telegram_id: int,
    role: str,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'superadmin')

    allowed = {'user', 'support', 'admin', 'superadmin'}
    role = role.lower()
    if role not in allowed:
        raise HTTPException(status_code=400, detail='Invalid role')

    target = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not target:
        target = User(telegram_id=telegram_id, role=role)
        db.add(target)
    else:
        target.role = role
    db.commit()
    return {'ok': True, 'telegram_id': telegram_id, 'role': role}


@router.post('/admin/users/ban')
def ban_user(
    telegram_id: int,
    ban: bool = True,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'support')

    target = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not target:
        target = User(telegram_id=telegram_id, is_banned=ban)
        db.add(target)
    else:
        target.is_banned = ban
    db.commit()
    return {'ok': True, 'telegram_id': telegram_id, 'is_banned': ban}


@router.get('/admin/orders')
def admin_orders(
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'support')

    data = db.query(Order).order_by(Order.id.desc()).limit(200).all()
    return {
        'count': len(data),
        'orders': [
            {
                'client_order_id': o.client_order_id,
                'user_id': o.user_id,
                'provider': o.provider_name,
                'status': o.status,
                'amount': str(o.charge_amount),
            }
            for o in data
        ],
    }


@router.get('/services/catalog')
def services_catalog(platform: str | None = None, db: Session = Depends(get_db)) -> dict:
    q = db.query(ServiceCatalog).filter(ServiceCatalog.enabled == True)  # noqa: E712
    if platform:
        q = q.filter(ServiceCatalog.platform == platform)
    data = q.order_by(ServiceCatalog.id.desc()).limit(1000).all()
    return {
        'count': len(data),
        'services': [
            {
                'id': x.id,
                'provider_name': x.provider_name,
                'provider_service_id': x.provider_service_id,
                'platform': x.platform,
                'category': x.category,
                'service_name': x.service_name,
                'base_rate': str(x.base_rate),
                'min_qty': x.min_qty,
                'max_qty': x.max_qty,
            }
            for x in data
        ],
    }


@router.get('/orders/track/{client_order_id}')
async def order_track(client_order_id: str, db: Session = Depends(get_db)) -> dict:
    order = db.query(Order).filter(Order.client_order_id == client_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    status = await refresh_order_status(order)
    db.commit()
    return {
        'client_order_id': order.client_order_id,
        'provider_order_id': order.provider_order_id,
        'provider_name': order.provider_name,
        'status': status,
    }


@router.post('/orders/refill/{client_order_id}')
async def order_refill(
    client_order_id: str,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    order = db.query(Order).filter(Order.client_order_id == client_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    if actor.role == 'user' and actor.id != order.user_id:
        raise HTTPException(status_code=403, detail='Not your order')

    result = await request_refill(order)
    return {'ok': True, 'result': result, 'client_order_id': client_order_id}


@router.post('/orders/cancel/{client_order_id}')
async def order_cancel(
    client_order_id: str,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    order = db.query(Order).filter(Order.client_order_id == client_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    if actor.role == 'user' and actor.id != order.user_id:
        raise HTTPException(status_code=403, detail='Not your order')

    result = await request_cancel(order)
    if result.get('status') in {'success', 'cancelled', 'canceled'}:
        order.status = 'cancelled'
        db.commit()
    return {'ok': True, 'result': result, 'client_order_id': client_order_id}


@router.post('/admin/orders/retry/{client_order_id}')
async def admin_order_retry(
    client_order_id: str,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'admin')

    order = db.query(Order).filter(Order.client_order_id == client_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')

    result = await place_order(order.service_id, order.link, order.quantity, base_rate=1.0)
    if result.get('status') == 'created':
        order.provider_name = result['provider']
        order.provider_order_id = result.get('provider_order_id')
        order.status = 'created'
        db.commit()
    return {'ok': True, 'retry_result': result, 'client_order_id': client_order_id}


@router.get('/admin/finance/report/daily')
def admin_finance_daily_report(
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'admin')
    data = fetch_finance_daily_report(db)
    return {'count': len(data), 'rows': data}


@router.post('/tickets')
def ticket_create(
    telegram_id: int,
    subject: str,
    message: str,
    db: Session = Depends(get_db),
) -> dict:
    t = create_ticket(db, telegram_id=telegram_id, subject=subject, message=message)
    return {'ok': True, 'ticket_ref': t.ticket_ref, 'status': t.status}


@router.get('/tickets/{telegram_id}')
def ticket_list(telegram_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {'count': 0, 'tickets': []}
    items = db.query(Ticket).filter(Ticket.user_id == user.id).order_by(Ticket.id.desc()).all()
    return {'count': len(items), 'tickets': [{'ticket_ref': i.ticket_ref, 'subject': i.subject, 'status': i.status, 'priority': i.priority} for i in items]}


@router.get('/tickets/messages/{ticket_ref}')
def ticket_messages(
    ticket_ref: str,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    t = db.query(Ticket).filter(Ticket.ticket_ref == ticket_ref).first()
    if not t:
        raise HTTPException(status_code=404, detail='Ticket not found')
    if actor.role == 'user' and actor.id != t.user_id:
        raise HTTPException(status_code=403, detail='Not your ticket')
    msgs = db.query(TicketMessage).filter(TicketMessage.ticket_id == t.id).order_by(TicketMessage.id.asc()).all()
    return {'ticket_ref': ticket_ref, 'count': len(msgs), 'messages': [{'sender_user_id': m.sender_user_id, 'message': m.message, 'is_staff': m.is_staff} for m in msgs]}


@router.post('/admin/tickets/reply/{ticket_ref}')
def admin_ticket_reply(
    ticket_ref: str,
    message: str,
    close_ticket: bool = False,
    x_telegram_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    actor = get_actor(db, x_telegram_id)
    require_role(actor, 'support')
    t = db.query(Ticket).filter(Ticket.ticket_ref == ticket_ref).first()
    if not t:
        raise HTTPException(status_code=404, detail='Ticket not found')
    db.add(TicketMessage(ticket_id=t.id, sender_user_id=actor.id, message=message, is_staff=True))
    if close_ticket:
        t.status = 'closed'
    else:
        t.status = 'open'
    db.commit()
    return {'ok': True, 'ticket_ref': ticket_ref, 'status': t.status}
        add_ledger_entry(db, user.id, 'credit', amount, reference_id=str(payload.get('order_id', 'cashfree')))
        db.commit()
    return {'ok': True}
@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.environment}


@router.get("/config/summary")
def config_summary() -> dict:
    return {
        "project_name": settings.project_name,
        "bot_username": settings.telegram_bot_username,
        "support_username": settings.telegram_support_username,
        "payment_gateway": settings.payment_gateway,
        "cashfree_mode": settings.cashfree_mode,
        "timezone": settings.timezone,
    }


@router.get("/services/platforms")
def services_platforms() -> dict:
    return {"platforms": platform_catalog(), "count": len(platform_catalog())}


@router.post("/orders/place")
async def orders_place(payload: CreateOrderRequest) -> dict:
    # base_rate placeholder until provider service sync table is added
    base_rate = 1.0
    result = await place_order(
        service_id=payload.service_id,
        link=payload.link,
        quantity=payload.quantity,
        base_rate=base_rate,
        category=None,
    )
    return result
