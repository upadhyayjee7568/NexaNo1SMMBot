from app.services.refund_engine import TERMINAL_FAILED_STATES


def test_terminal_states_contains_failed():
    assert "failed" in TERMINAL_FAILED_STATES
    assert "canceled" in TERMINAL_FAILED_STATES or "cancelled" in TERMINAL_FAILED_STATES
