from app.services.order_lifecycle import normalize_status


def test_normalize_status_completed():
    assert normalize_status('Completed') == 'completed'


def test_normalize_status_unknown():
    assert normalize_status('SomeNewState') == 'somenewstate'
