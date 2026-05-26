from decimal import Decimal
from app.services.growth import vip_discount_percent


def test_vip_discount_levels():
    assert vip_discount_percent(Decimal('500')) == Decimal('0')
    assert vip_discount_percent(Decimal('10000')) == Decimal('2')
    assert vip_discount_percent(Decimal('50000')) == Decimal('5')
    assert vip_discount_percent(Decimal('100000')) == Decimal('10')
