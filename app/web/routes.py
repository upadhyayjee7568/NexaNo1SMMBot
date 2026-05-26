import csv
import io

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.routes import get_db
from app.core.settings import settings
from app.db.models import Coupon, Order, PaymentTransaction, ServiceCatalog, Ticket, User
from app.services.auth import create_session, get_session, require_admin_user, require_csrf
from app.services.growth import apply_coupon

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


def _session(request: Request, db: Session):
    return get_session(db, request.cookies.get(settings.web_session_cookie_name))


@router.get('/web/login')
def web_login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request, 'result': None})


@router.post('/web/login')
def web_login(request: Request, telegram_id: int = Form(...), db: Session = Depends(get_db)):
    sess = create_session(db, telegram_id=telegram_id)
    resp = RedirectResponse(url='/app', status_code=302)
    resp.set_cookie(settings.web_session_cookie_name, sess.session_token, httponly=True, samesite='lax')
    resp.set_cookie('csrf_token', sess.csrf_token, httponly=False, samesite='lax')
    return resp


@router.get('/app')
def customer_home(request: Request, db: Session = Depends(get_db)):
    _session(request, db)
    return templates.TemplateResponse('customer.html', {'request': request, 'result': None})


@router.get('/app/wallet')
def app_wallet(request: Request, telegram_id: int, db: Session = Depends(get_db)):
    from app.services.wallet import wallet_balance
    _session(request, db)
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    bal = "0.00" if not u else str(wallet_balance(db, u.id))
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'wallet={bal} INR'})


@router.post('/app/coupon/apply')
def app_coupon_apply(request: Request, code: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    final, status = apply_coupon(db, code=code, amount=amount)
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'{status}: final={final}'})


@router.get('/admin')
def admin_home(request: Request, db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_admin_user(db, sess)
    return templates.TemplateResponse('admin.html', {'request': request, 'result': None})


@router.get('/admin/users')
def admin_users(request: Request, db: Session = Depends(get_db)):
    require_admin_user(db, _session(request, db))
    users = db.query(User).order_by(User.id.desc()).limit(200).all()
    return templates.TemplateResponse('admin_users.html', {'request': request, 'users': users})


@router.get('/admin/payments')
def admin_payments(request: Request, db: Session = Depends(get_db)):
    require_admin_user(db, _session(request, db))
    payments = db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(200).all()
    return templates.TemplateResponse('admin_payments.html', {'request': request, 'payments': payments})


@router.get('/admin/services')
def admin_services(request: Request, db: Session = Depends(get_db)):
    require_admin_user(db, _session(request, db))
    services = db.query(ServiceCatalog).order_by(ServiceCatalog.id.desc()).limit(500).all()
    return templates.TemplateResponse('admin_services.html', {'request': request, 'services': services})


@router.get('/admin/tickets')
def admin_tickets(request: Request, db: Session = Depends(get_db)):
    require_admin_user(db, _session(request, db))
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).limit(500).all()
    return templates.TemplateResponse('admin_tickets.html', {'request': request, 'tickets': tickets})


@router.post('/admin/coupons/create')
def admin_coupon_create(request: Request, code: str = Form(...), discount: float = Form(...), db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    require_admin_user(db, sess)
    c = Coupon(code=code.upper(), discount_percent=discount)
    db.add(c)
    db.commit()
    return templates.TemplateResponse('admin.html', {'request': request, 'result': f'Coupon created: {c.code}'})


@router.get('/admin/reports/export/csv')
def admin_export_csv(request: Request, kind: str = 'orders', db: Session = Depends(get_db)):
    require_admin_user(db, _session(request, db))
    output = io.StringIO()
    writer = csv.writer(output)
    if kind == 'orders':
        writer.writerow(['client_order_id', 'user_id', 'provider', 'status', 'charge_amount'])
        for o in db.query(Order).order_by(Order.id.desc()).limit(5000):
            writer.writerow([o.client_order_id, o.user_id, o.provider_name, o.status, o.charge_amount])
    elif kind == 'payments':
        writer.writerow(['id', 'gateway', 'event_id', 'amount', 'status'])
        for p in db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(5000):
            writer.writerow([p.id, p.gateway, p.gateway_event_id, p.amount, p.status])
    return StreamingResponse(iter([output.getvalue().encode()]), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename={kind}.csv'})
