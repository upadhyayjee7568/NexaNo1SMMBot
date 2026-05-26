from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import User, WebSession

SESSION_HOURS = 12


def create_session(db: Session, telegram_id: int) -> WebSession:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
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
