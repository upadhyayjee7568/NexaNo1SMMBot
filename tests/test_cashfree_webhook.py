from fastapi import HTTPException

from app.services.cashfree_webhook import is_success_event, extract_event_id


def test_success_event_true():
    assert is_success_event("PAID")
    assert is_success_event("success")


def test_success_event_false():
    assert not is_success_event("FAILED")
    assert not is_success_event(None)


def test_extract_event_id_prefers_payment_fields():
    assert extract_event_id({"cf_payment_id": "cf_1", "order_id": "o_1"}) == "cf_1"


def test_extract_event_id_fallback_order_id():
    assert extract_event_id({"order_id": "ord_abc"}) == "ord_abc"


def test_extract_event_id_missing_raises():
    try:
        extract_event_id({})
        assert False
    except HTTPException as exc:
        assert exc.status_code == 400
