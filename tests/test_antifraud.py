from app.services.antifraud import detect_blocked_words


def test_detect_blocked_words():
    found = detect_blocked_words('need hack and spam service')
    assert 'hack' in found
    assert 'spam' in found
