from decimal import Decimal


def test_decimal_abs_for_journal_amount():
    assert abs(Decimal('-10.50')) == Decimal('10.50')
