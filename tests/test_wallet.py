from decimal import Decimal

from app.services.wallet import _normalized_amount


def test_normalized_amount_credit_positive():
    assert _normalized_amount("credit", Decimal("100")) == Decimal("100")


def test_normalized_amount_debit_negative():
    assert _normalized_amount("debit", Decimal("100")) == Decimal("-100")


def test_normalized_amount_debit_negative_input_kept_negative():
    assert _normalized_amount("debit", Decimal("-50")) == Decimal("-50")
