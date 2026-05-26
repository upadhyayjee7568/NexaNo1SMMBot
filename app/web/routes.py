import io, csv
from fastapi import APIRouter, Form, Request, Response, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi import APIRouter, Form, Request, Response, Depends
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.routes import get_db
from app.core.settings import settings
from app.services.auth import create_session, get_session, require_csrf, require_admin_user
from app.db.models import Order, User, Coupon, PaymentTransaction, ServiceCatalog, Ticket
from app.services.growth import apply_coupon
from app.services.finance import fetch_finance_daily_report
from app.db.models import Order, User, Coupon
from app.services.growth import apply_coupon
from app.services.finance import fetch_finance_daily_report
from app.db.models import Order
from app.services.growth import apply_coupon
from app.services.finance import fetch_finance_daily_report
from app.db.models import Coupon

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


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


def _session(request: Request, db: Session) -> tuple:
    tok = request.cookies.get(settings.web_session_cookie_name)
    sess = get_session(db, tok)
    return tok, sess


@router.get('/app')
def customer_home(request: Request, db: Session = Depends(get_db)):
    _session(request, db)
@router.get('/app')
def customer_home(request: Request):
    return templates.TemplateResponse('customer.html', {'request': request, 'result': None})


@router.get('/app/wallet')
def app_wallet(request: Request, telegram_id: int, db: Session = Depends(get_db)):
    _session(request, db)
    from app.services.wallet import wallet_balance
def app_wallet(request: Request, telegram_id: int, db: Session = next(get_db())):
    from app.services.wallet import wallet_balance
    from app.db.models import User
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    bal = "0.00" if not u else str(wallet_balance(db, u.id))
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'wallet={bal} INR'})


@router.get('/app/orders')
def app_orders(request: Request, telegram_id: int, db: Session = Depends(get_db)):
    _session(request, db)
def app_orders(request: Request, telegram_id: int, db: Session = next(get_db())):
    from app.db.models import User
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not u:
        return templates.TemplateResponse('customer.html', {'request': request, 'result': 'No user/orders'})
    rows = db.query(Order).filter(Order.user_id == u.id).order_by(Order.id.desc()).limit(20).all()
    result = '\n'.join([f"{x.client_order_id} | {x.status} | {x.charge_amount}" for x in rows]) or 'No orders'
    return templates.TemplateResponse('customer.html', {'request': request, 'result': result})


@router.post('/app/coupon/apply')
def app_coupon_apply(request: Request, code: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_csrf(request, sess)
def app_coupon_apply(request: Request, code: str = Form(...), amount: float = Form(...), db: Session = next(get_db())):
    final, status = apply_coupon(db, code=code, amount=amount)
    return templates.TemplateResponse('customer.html', {'request': request, 'result': f'{status}: final={final}'})


@router.get('/admin')
def admin_home(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
def admin_home(request: Request):
    return templates.TemplateResponse('admin.html', {'request': request, 'result': None})


@router.get('/admin/finance')
def admin_finance(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
def admin_finance(request: Request, admin_tg: int, db: Session = next(get_db())):
    # kept simple for web panel demo; API has full RBAC checks
    rows = fetch_finance_daily_report(db)
    return templates.TemplateResponse('admin.html', {'request': request, 'result': rows})


@router.post('/admin/coupons/create')
def admin_coupon_create(request: Request, code: str = Form(...), discount: float = Form(...), db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_csrf(request, sess)
    require_admin_user(db, sess)
def admin_coupon_create(request: Request, admin_tg: int = Form(...), code: str = Form(...), discount: float = Form(...), db: Session = next(get_db())):
    c = Coupon(code=code.upper(), discount_percent=discount)
    db.add(c)
    db.commit()
    return templates.TemplateResponse('admin.html', {'request': request, 'result': f'Coupon created: {c.code}'})


@router.get('/admin/orders/view')
def admin_orders_view(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    rows = db.query(Order).order_by(Order.id.desc()).limit(50).all()
    result = '\n'.join([f"{x.client_order_id} | user={x.user_id} | {x.status} | {x.charge_amount}" for x in rows]) or 'No orders'
    return templates.TemplateResponse('admin.html', {'request': request, 'result': result})


@router.get('/admin/users')
def admin_users(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    users = db.query(User).order_by(User.id.desc()).limit(200).all()
    return templates.TemplateResponse('admin_users.html', {'request': request, 'users': users})


@router.get('/admin/payments')
def admin_payments(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    payments = db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(200).all()
    return templates.TemplateResponse('admin_payments.html', {'request': request, 'payments': payments})


@router.get('/admin/services')
def admin_services(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    services = db.query(ServiceCatalog).order_by(ServiceCatalog.id.desc()).limit(500).all()
    return templates.TemplateResponse('admin_services.html', {'request': request, 'services': services})


@router.get('/admin/tickets')
def admin_tickets(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).limit(500).all()
    return templates.TemplateResponse('admin_tickets.html', {'request': request, 'tickets': tickets})


@router.get('/admin/settings')
def admin_settings(request: Request, db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    return templates.TemplateResponse('admin_settings.html', {'request': request})


@router.get('/admin/reports/export/csv')
def admin_export_csv(request: Request, kind: str = 'orders', db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    output = io.StringIO()
    writer = csv.writer(output)
    if kind == 'orders':
        writer.writerow(['client_order_id','user_id','provider','status','charge_amount'])
        for o in db.query(Order).order_by(Order.id.desc()).limit(5000):
            writer.writerow([o.client_order_id,o.user_id,o.provider_name,o.status,o.charge_amount])
    elif kind == 'payments':
        writer.writerow(['id','gateway','event_id','amount','status'])
        for p in db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(5000):
            writer.writerow([p.id,p.gateway,p.gateway_event_id,p.amount,p.status])
    else:
        writer.writerow(['unsupported_kind'])
    data = output.getvalue().encode()
    return StreamingResponse(iter([data]), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename={kind}.csv'})


@router.get('/admin/reports/export/pdf')
def admin_export_pdf(request: Request, kind: str = 'orders', db: Session = Depends(get_db)):
    _, sess = _session(request, db)
    require_admin_user(db, sess)
    # lightweight text/pdf-compatible stream (placeholder report format)
    lines = [f'Nexa Report: {kind}', '-------------------------']
    if kind == 'orders':
        for o in db.query(Order).order_by(Order.id.desc()).limit(200):
            lines.append(f"{o.client_order_id} | {o.status} | {o.charge_amount}")
    elif kind == 'payments':
        for p in db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(200):
            lines.append(f"{p.id} | {p.gateway} | {p.amount} | {p.status}")
    payload = ('\n'.join(lines)).encode()
    return StreamingResponse(iter([payload]), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename={kind}.pdf'})
def admin_orders_view(request: Request, admin_tg: int, db: Session = next(get_db())):
    rows = db.query(Order).order_by(Order.id.desc()).limit(50).all()
    result = '\n'.join([f"{x.client_order_id} | user={x.user_id} | {x.status} | {x.charge_amount}" for x in rows]) or 'No orders'
    return templates.TemplateResponse('admin.html', {'request': request, 'result': result})
