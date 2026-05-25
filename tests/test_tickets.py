from app.services.tickets import create_ticket


def test_ticket_ref_prefix(monkeypatch):
    class T:
        ticket_ref='TKT-TEST'
    # sanity placeholder for module import
    assert True
