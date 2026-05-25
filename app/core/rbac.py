from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User

ROLE_LEVEL = {
    "user": 0,
    "support": 1,
    "admin": 2,
    "superadmin": 3,
}


def get_actor(db: Session, x_telegram_id: int | None) -> User:
    if not x_telegram_id:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Id header")
    actor = db.query(User).filter(User.telegram_id == x_telegram_id).first()
    if not actor:
        raise HTTPException(status_code=401, detail="Actor not found")
    if actor.is_banned:
        raise HTTPException(status_code=403, detail="Actor is banned")
    return actor


def require_role(actor: User, min_role: str) -> None:
    current = ROLE_LEVEL.get((actor.role or "user").lower(), 0)
    needed = ROLE_LEVEL[min_role]
    if current < needed:
        raise HTTPException(status_code=403, detail=f"Requires role: {min_role}")
