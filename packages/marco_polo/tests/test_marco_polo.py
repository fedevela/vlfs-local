from marco_polo import play_game

def test_play_game():
    assert play_game("marco") == "polo"
    assert play_game("Marco") == "polo"
    assert play_game("MARCO") == "polo"
    assert play_game("pizza") == "i-cant-help-with-that"
    assert play_game("polo") == "i-cant-help-with-that"
