from app.services.pricing import apply_markup


def test_apply_markup_default():
    assert apply_markup(100.0) == 125.0


def test_apply_markup_category():
    assert apply_markup(100.0, "youtube_views") == 130.0
