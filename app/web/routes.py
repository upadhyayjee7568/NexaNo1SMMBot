from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.routes import get_db
from app.db.models import Order
from app.services.growth import apply_coupon
from app.services.finance import fetch_finance_daily_report
from app.db.models import Coupon

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get('/app')
def customer_home(request: Request):
    return templates.TemplateResponse('customer.html', {'request': request, 'result': None})


@router.get('/app/wallet')
def app_wallet(request: Request, telegram_id: int, db: Session = next(get_db())):
    from app.services.wallet import wallet_balance
    from app.db.models import User
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    bal = "0.00" if not u else str(wallet_balance(db, u.id))
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'wallet={bal} INR'})


@router.get('/app/orders')
def app_orders(request: Request, telegram_id: int, db: Session = next(get_db())):
    from app.db.models import User
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not u:
        return templates.TemplateResponse('customer.html', {'request': request, 'result': 'No user/orders'})
    rows = db.query(Order).filter(Order.user_id == u.id).order_by(Order.id.desc()).limit(20).all()
    result = '\n'.join([f"{x.client_order_id} | {x.status} | {x.charge_amount}" for x in rows]) or 'No orders'
    return templates.TemplateResponse('customer.html', {'request': request, 'result': result})


@router.post('/app/coupon/apply')
def app_coupon_apply(request: Request, code: str = Form(...), amount: float = Form(...), db: Session = next(get_db())):
    final, status = apply_coupon(db, code=code, amount=amount)
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'{status}: final={final}'})


@router.get('/admin')
def admin_home(request: Request):
    return templates.TemplateResponse('admin.html', {'request': request, 'result': None})


@router.get('/admin/finance')
def admin_finance(request: Request, admin_tg: int, db: Session = next(get_db())):
    # kept simple for web panel demo; API has full RBAC checks
    rows = fetch_finance_daily_report(db)
    return templates.TemplateResponse('admin.html', {'request': request, 'result': rows})


@router.post('/admin/coupons/create')
def admin_coupon_create(request: Request, admin_tg: int = Form(...), code: str = Form(...), discount: float = Form(...), db: Session = next(get_db())):
    c = Coupon(code=code.upper(), discount_percent=discount)
    db.add(c)
    db.commit()
    return templates.TemplateResponse('admin.html', {'request': request, 'result': f'Coupon created: {c.code}'})


@router.get('/admin/orders/view')
def admin_orders_view(request: Request, admin_tg: int, db: Session = next(get_db())):
    rows = db.query(Order).order_by(Order.id.desc()).limit(50).all()
    result = '\n'.join([f"{x.client_order_id} | user={x.user_id} | {x.status} | {x.charge_amount}" for x in rows]) or 'No orders'
    return templates.TemplateResponse('admin.html', {'request': request, 'result': result})
