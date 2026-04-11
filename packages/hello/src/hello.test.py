from hello import get_greeting

def test_get_greeting():
    assert get_greeting() == "Hello from the isolated module!"
