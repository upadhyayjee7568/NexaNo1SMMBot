import hashlib
import hmac

from app.services.cashfree_webhook import is_success_event


def test_success_event_true():
    assert is_success_event("PAID")
    assert is_success_event("success")


def test_success_event_false():
    assert not is_success_event("FAILED")
    assert not is_success_event(None)
