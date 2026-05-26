from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Coupon, DailyReward, Referral, User
from app.services.wallet import add_ledger_entry

VIP_DISCOUNTS = {"silver": Decimal("2"), "gold": Decimal("5"), "platinum": Decimal("10")}


def vip_discount_percent(total_spend: Decimal) -> Decimal:
    if total_spend >= Decimal("100000"):
        return VIP_DISCOUNTS["platinum"]
    if total_spend >= Decimal("50000"):
        return VIP_DISCOUNTS["gold"]
    if total_spend >= Decimal("10000"):
        return VIP_DISCOUNTS["silver"]
    return Decimal("0")


def apply_coupon(db: Session, code: str, amount: Decimal) -> tuple[Decimal, str]:
    c = db.query(Coupon).filter(Coupon.code == code.upper(), Coupon.active == True).first()  # noqa: E712
    if not c:
        return amount, "invalid_coupon"
    if c.max_uses is not None and c.used_count >= c.max_uses:
        return amount, "coupon_exhausted"
    discount = (Decimal(str(c.discount_percent)) / Decimal("100")) * amount
    c.used_count += 1
    db.commit()
    return max(Decimal("0"), amount - discount), "coupon_applied"


def register_referral(db: Session, referrer_tg: int, referred_tg: int, percent: Decimal = Decimal("5")) -> str:
    referrer = db.query(User).filter(User.telegram_id == referrer_tg).first()
    referred = db.query(User).filter(User.telegram_id == referred_tg).first()
    if not referrer or not referred:
        return "missing_user"
    exists = db.query(Referral).filter(Referral.referred_user_id == referred.id).first()
    if exists:
        return "already_referred"
    db.add(Referral(referrer_user_id=referrer.id, referred_user_id=referred.id, reward_percent=percent))
    db.commit()
    return "ok"


def credit_daily_reward(db: Session, telegram_id: int, amount: Decimal = Decimal("2")) -> str:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return "missing_user"
    today = date.today()
    exists = db.query(DailyReward).filter(DailyReward.user_id == user.id, DailyReward.reward_date >= datetime(today.year,today.month,today.day)).first()
    if exists:
        return "already_claimed"
    db.add(DailyReward(user_id=user.id, reward_date=datetime(today.year,today.month,today.day), amount=amount))
    add_ledger_entry(db, user.id, 'credit', amount, reference_id=f'daily:{today.isoformat()}', note='Daily reward')
    db.commit()
    return "claimed"
