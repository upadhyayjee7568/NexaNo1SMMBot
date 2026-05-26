from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models import FraudEvent, User

BLOCKED_WORDS = {"spam", "abuse", "hack", "fraud"}


def _ensure_user(db: Session, telegram_id: int) -> User:
    u = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not u:
        u = User(telegram_id=telegram_id)
        db.add(u)
        db.flush()
    return u


def log_event(db: Session, user_id: int, event_type: str, risk_score: int, details: str | None = None) -> FraudEvent:
    ev = FraudEvent(user_id=user_id, event_type=event_type, risk_score=risk_score, details=details)
    db.add(ev)
    db.flush()
    return ev


def detect_blocked_words(text: str) -> list[str]:
    raw = (text or "").lower()
    return sorted([w for w in BLOCKED_WORDS if w in raw])


def check_rate_limit(db: Session, user_id: int, event_type: str, limit: int, window_seconds: int) -> bool:
    since = datetime.utcnow() - timedelta(seconds=window_seconds)
    count = (
        db.query(FraudEvent)
        .filter(FraudEvent.user_id == user_id, FraudEvent.event_type == event_type, FraudEvent.created_at >= since)
        .count()
    )
    return count >= limit


def compute_user_risk(db: Session, user_id: int) -> int:
    rows = db.query(FraudEvent).filter(FraudEvent.user_id == user_id).order_by(FraudEvent.id.desc()).limit(50).all()
    score = sum(r.risk_score for r in rows)
    return int(score)


def evaluate_order_text_risk(db: Session, telegram_id: int, text: str) -> tuple[int, list[str], bool]:
    user = _ensure_user(db, telegram_id)

    bad_words = detect_blocked_words(text)
    risk = len(bad_words) * 25

    if check_rate_limit(db, user.id, 'order_attempt', limit=20, window_seconds=300):
        risk += 30

    if bad_words:
        log_event(db, user.id, 'blocked_words', min(100, risk), ','.join(bad_words))

    log_event(db, user.id, 'order_attempt', min(100, risk), text[:200])
    db.commit()

    total_risk = compute_user_risk(db, user.id)
    auto_block = total_risk >= 200
    if auto_block and not user.is_banned:
        user.is_banned = True
        db.commit()

    return total_risk, bad_words, auto_block
