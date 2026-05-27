from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Ticket, TicketMessage, User


ALLOWED_STAFF_ROLES = {"support", "admin", "superadmin"}


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
    db.refresh(t)
    return t


def list_tickets_by_telegram(db: Session, telegram_id: int) -> list[Ticket]:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []
    return db.query(Ticket).filter(Ticket.user_id == user.id).order_by(Ticket.id.desc()).all()


def list_ticket_messages(db: Session, ticket_ref: str, actor_telegram_id: int) -> list[TicketMessage]:
    ticket = db.query(Ticket).filter(Ticket.ticket_ref == ticket_ref).first()
    if not ticket:
        return []
    actor = db.query(User).filter(User.telegram_id == actor_telegram_id).first()
    if not actor:
        return []
    is_staff = (actor.role or "user").lower() in ALLOWED_STAFF_ROLES
    if not is_staff and ticket.user_id != actor.id:
        return []
    return db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket.id).order_by(TicketMessage.id.asc()).all()


def reply_ticket(
    db: Session,
    ticket_ref: str,
    actor_telegram_id: int,
    message: str,
    close_ticket: bool = False,
) -> TicketMessage | None:
    ticket = db.query(Ticket).filter(Ticket.ticket_ref == ticket_ref).first()
    if not ticket:
        return None
    actor = _ensure_user(db, actor_telegram_id)
    is_staff = (actor.role or "user").lower() in ALLOWED_STAFF_ROLES
    if not is_staff and ticket.user_id != actor.id:
        return None

    msg = TicketMessage(ticket_id=ticket.id, sender_user_id=actor.id, message=message, is_staff=is_staff)
    db.add(msg)
    if close_ticket and is_staff:
        ticket.status = "closed"
    db.commit()
    db.refresh(msg)
    return msg
