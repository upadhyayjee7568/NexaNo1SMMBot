from app.services.catalog_sync import detect_platform


def test_detect_platform():
    assert detect_platform("Instagram Followers", None) == "Instagram"
    assert detect_platform("High Retention Views", "YouTube") == "YouTube"
    assert detect_platform("Members", "Telegram") == "Telegram"
