def play_game(phrase: str) -> str:
    """Evaluates the input phrase against the game rules."""
    if phrase.strip().lower() == "marco":
        return "polo"
    return "i-cant-help-with-that"
