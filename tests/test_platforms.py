from app.services.platforms import platform_catalog


def test_platform_catalog_non_empty():
    data = platform_catalog()
    assert len(data) > 0
    assert any(x["platform"] == "Instagram" for x in data)
    assert any(x["platform"] == "Facebook" for x in data)
