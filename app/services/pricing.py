from decimal import Decimal

CATEGORY_MARKUP = {
    "instagram_followers": Decimal("20"),
    "instagram_likes": Decimal("25"),
    "youtube_views": Decimal("30"),
    "telegram_members": Decimal("20"),
}
DEFAULT_MARKUP = Decimal("25")


def resolve_category(platform: str, service_name: str) -> str | None:
    p = (platform or '').lower()
    s = (service_name or '').lower()
    if 'instagram' in p and 'follower' in s:
        return 'instagram_followers'
    if 'instagram' in p and 'like' in s:
        return 'instagram_likes'
    if 'youtube' in p and 'view' in s:
        return 'youtube_views'
    if 'telegram' in p and 'member' in s:
        return 'telegram_members'
    return None


def apply_markup(base_rate: Decimal | float, category: str | None = None) -> Decimal:
    base = Decimal(str(base_rate))
    markup = CATEGORY_MARKUP.get(category or "", DEFAULT_MARKUP)
    return (base * (Decimal("1") + markup / Decimal("100"))).quantize(Decimal("0.0001"))


def compute_final_amount(
    base_rate: Decimal,
    quantity: int,
    category: str | None,
    vip_discount_percent: Decimal = Decimal('0'),
    coupon_discount_percent: Decimal = Decimal('0'),
    user_bear_fee_percent: Decimal = Decimal('0'),
) -> Decimal:
    unit = apply_markup(base_rate, category)
    gross = unit * Decimal(quantity)
    discount_pct = vip_discount_percent + coupon_discount_percent
    discount_amt = gross * discount_pct / Decimal('100')
    net = gross - discount_amt
    fee = net * user_bear_fee_percent / Decimal('100')
    return (net + fee).quantize(Decimal('0.01'))
