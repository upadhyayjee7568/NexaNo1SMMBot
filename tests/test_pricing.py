from decimal import Decimal
from app.services.pricing import compute_final_amount


def test_compute_final_amount_with_discounts_and_fee():
    amount = compute_final_amount(
        base_rate=Decimal('10'),
        quantity=10,
        category='instagram_followers',
        vip_discount_percent=Decimal('2'),
        coupon_discount_percent=Decimal('5'),
        user_bear_fee_percent=Decimal('2'),
    )
    assert amount > Decimal('0')
from app.services.pricing import apply_markup


def test_apply_markup_default():
    assert apply_markup(100.0) == 125.0


def test_apply_markup_category():
    assert apply_markup(100.0, "youtube_views") == 130.0
