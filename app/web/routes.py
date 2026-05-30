import csv
import io

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.routes import get_db
from app.core.settings import settings
from app.db.models import Coupon, Order, PaymentTransaction, ServiceCatalog, Ticket, UpiTopup, User
from app.services.auth import create_session, get_session, require_admin_access, require_csrf
from app.services.growth import apply_coupon
from app.services.health_monitor import get_health_status

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


def _session(request: Request, db: Session):
    return get_session(db, request.cookies.get(settings.web_session_cookie_name))


def _session_user(request: Request, db: Session) -> User:
    sess = _session(request, db)
    user = db.query(User).filter(User.id == sess.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Session user missing")
    return user


@router.get("/web/login")
def web_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "result": None})


@router.post("/web/login")
def web_login(request: Request, telegram_id: int = Form(...), db: Session = Depends(get_db)):
    sess = create_session(db, telegram_id=telegram_id)
    resp = RedirectResponse(url="/app", status_code=302)
    resp.set_cookie(settings.web_session_cookie_name, sess.session_token, httponly=True, samesite="lax")
    resp.set_cookie("csrf_token", sess.csrf_token, httponly=False, samesite="lax")
    return resp


@router.get("/app")
def customer_home(request: Request, db: Session = Depends(get_db)):
    user = _session_user(request, db)
    bal = str(wallet_balance(db, user.id))
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).limit(20).all()
    return templates.TemplateResponse(
        "customer.html",
        {
            "request": request,
            "result": None,
            "user": user,
            "balance": bal,
            "orders": orders,
            "support_username": settings.telegram_support_username,
        },
    )


@router.get("/app/wallet")
def app_wallet(request: Request, db: Session = Depends(get_db)):
    user = _session_user(request, db)
    bal = str(wallet_balance(db, user.id))
    return templates.TemplateResponse(
        "customer.html",
        {"request": request, "result": f"wallet={bal} INR", "user": user, "balance": bal, "orders": []},
    )


@router.post("/app/coupon/apply")
def app_coupon_apply(request: Request, code: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    final, status = apply_coupon(db, code=code, amount=amount)
    return templates.TemplateResponse("customer.html", {"request": request, "result": f"{status}: final={final}"})


@router.get("/admin")
def admin_home(request: Request, db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_admin_access(request, db, sess)
    users_count = db.query(User).count()
    orders_count = db.query(Order).count()
    payments_count = db.query(PaymentTransaction).count()
    pending_upi = db.query(UpiTopup).filter(UpiTopup.status == "pending").count()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "result": None,
            "stats": {
                "users": users_count,
                "orders": orders_count,
                "payments": payments_count,
                "pending_upi": pending_upi,
            },
        },
    )


@router.get("/admin/users")
def admin_users(request: Request, db: Session = Depends(get_db)):
    require_admin_access(request, db, _session(request, db))
    users = db.query(User).order_by(User.id.desc()).limit(200).all()
    return templates.TemplateResponse("admin_users.html", {"request": request, "users": users})


@router.get("/admin/payments")
def admin_payments(request: Request, db: Session = Depends(get_db)):
    require_admin_access(request, db, _session(request, db))
    payments = db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(200).all()
    upi = db.query(UpiTopup).order_by(UpiTopup.id.desc()).limit(200).all()
    return templates.TemplateResponse(
        "admin_payments.html", {"request": request, "payments": payments, "upi_topups": upi}
    )


@router.post("/admin/upi/{topup_id}/approve")
def admin_upi_approve(request: Request, topup_id: int, db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    require_admin_access(request, db, sess)
    from app.services.upi_fallback import credit_upi_topup

    topup = db.query(UpiTopup).filter(UpiTopup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=404, detail="Top-up not found")
    status = credit_upi_topup(db, topup, by="admin")
    db.commit()
    return RedirectResponse(url="/admin/payments", status_code=302)


@router.post("/admin/upi/{topup_id}/reject")
def admin_upi_reject(request: Request, topup_id: int, db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    require_admin_access(request, db, sess)
    topup = db.query(UpiTopup).filter(UpiTopup.id == topup_id).first()
    if not topup:
        raise HTTPException(status_code=404, detail="Top-up not found")
    if topup.status == "pending":
        topup.status = "rejected"
        db.commit()
    return RedirectResponse(url="/admin/payments", status_code=302)


@router.get("/admin/services")
def admin_services(request: Request, db: Session = Depends(get_db)):
    require_admin_access(request, db, _session(request, db))
    services = db.query(ServiceCatalog).order_by(ServiceCatalog.id.desc()).limit(500).all()
    return templates.TemplateResponse("admin_services.html", {"request": request, "services": services})


@router.get("/admin/tickets")
def admin_tickets(request: Request, db: Session = Depends(get_db)):
    require_admin_access(request, db, _session(request, db))
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).limit(500).all()
    return templates.TemplateResponse("admin_tickets.html", {"request": request, "tickets": tickets})


@router.post("/admin/coupons/create")
def admin_coupon_create(request: Request, code: str = Form(...), discount: float = Form(...), db: Session = Depends(get_db)):
    sess = _session(request, db)
    require_csrf(request, sess)
    require_admin_access(request, db, sess)
    c = Coupon(code=code.upper(), discount_percent=discount)
    db.add(c)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin/reports/export/csv")
def admin_export_csv(request: Request, kind: str = "orders", db: Session = Depends(get_db)):
    require_admin_access(request, db, _session(request, db))
    output = io.StringIO()
    writer = csv.writer(output)
    if kind == "orders":
        writer.writerow(["client_order_id", "user_id", "provider", "status", "charge_amount"])
        for o in db.query(Order).order_by(Order.id.desc()).limit(5000):
            writer.writerow([o.client_order_id, o.user_id, o.provider_name, o.status, o.charge_amount])
    elif kind == "payments":
        writer.writerow(["id", "gateway", "event_id", "amount", "status"])
        for p in db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(5000):
            writer.writerow([p.id, p.gateway, p.gateway_event_id, p.amount, p.status])
    return StreamingResponse(
        iter([output.getvalue().encode()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={kind}.csv"},
    )


@router.get("/health/dashboard")
def health_dashboard(request: Request, db: Session = Depends(get_db)):
    """Display system health status dashboard for admins."""
    sess = _session(request, db)
    require_admin_access(request, db, sess)
    
    health_status = get_health_status()
    
    return templates.TemplateResponse(
        "health_dashboard.html",
        {
            "request": request,
            "health": health_status,
        },
    )


@router.get("/web/logout")
def web_logout(request: Request):
    """Logout user and clear session cookie."""
    resp = RedirectResponse(url="/web/login", status_code=302)
    resp.delete_cookie(settings.web_session_cookie_name)
    resp.delete_cookie("csrf_token")
    return resp
