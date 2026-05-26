from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import User, WebSession

SESSION_HOURS = 12


def create_session(db: Session, telegram_id: int) -> WebSession:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    db.query(WebSession).filter(WebSession.user_id == user.id).delete()
    sess = WebSession(
        session_token=token_urlsafe(32),
        csrf_token=token_urlsafe(24),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_HOURS),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def get_session(db: Session, session_token: str | None) -> WebSession:
    if not session_token:
        raise HTTPException(status_code=401, detail='Missing session')
    sess = db.query(WebSession).filter(WebSession.session_token == session_token).first()
    if not sess or sess.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Invalid/expired session')
    return sess


def require_csrf(request: Request, sess: WebSession) -> None:
    csrf = request.headers.get('X-CSRF-Token') or request.query_params.get('csrf_token') or request.cookies.get('csrf_token')
    if csrf != sess.csrf_token:
        raise HTTPException(status_code=403, detail='CSRF validation failed')


def require_admin_user(db: Session, sess: WebSession) -> User:
    user = db.query(User).filter(User.id == sess.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail='User missing')
    if (user.role or 'user').lower() not in {'admin', 'superadmin', 'support'}:
        raise HTTPException(status_code=403, detail='Admin role required')
    return user



def require_admin_access(request: Request, db: Session, sess: WebSession) -> User:
    user = require_admin_user(db, sess)
    code = request.headers.get('X-Admin-2FA') or request.query_params.get('admin_2fa_code')
    validate_admin_2fa(user, code)
    if user.is_banned:
        raise HTTPException(status_code=403, detail='Admin account is banned')
    return user



def validate_admin_2fa(user: User, submitted_code: str | None) -> None:
    if not settings.admin_2fa_enabled:
        return
    if (user.role or "user").lower() not in {"admin", "superadmin"}:
        return
    if not settings.admin_2fa_code:
        raise HTTPException(status_code=500, detail='Admin 2FA misconfigured')
    if submitted_code != settings.admin_2fa_code:
        raise HTTPException(status_code=403, detail='Invalid admin 2FA code')
