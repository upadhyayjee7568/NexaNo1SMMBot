from __future__ import annotations

from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models import Ticket, TicketMessage, User


def _ensure_user(db: Session, telegram_id: int) -> User:
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not u:
        u = User(telegram_id=telegram_id)
        db.add(u)
        db.flush()
    return u


def create_ticket(db: Session, telegram_id: int, subject: str, message: str) -> Ticket:
    user = _ensure_user(db, telegram_id)
    t = Ticket(ticket_ref=f"TKT-{uuid4().hex[:10].upper()}", user_id=user.id, subject=subject)
    db.add(t)
    db.flush()
    db.add(TicketMessage(ticket_id=t.id, sender_user_id=user.id, message=message, is_staff=False))
    db.commit()
    return t
