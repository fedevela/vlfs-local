import sys
import os
from dotenv import load_dotenv

# Enforce loading .env exclusively from the project root ./.env
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)  # pragma: no cover

from hello import get_greeting
from marco_polo import play_game
from vlfs_mcp import run as run_mcp

def main():
    # If the user passes --mcp, start the VLFS server instead of the game engine
    if "--mcp" in sys.argv:  # pragma: no cover
        run_mcp()
        return

    # 1. Use the hello module
    print(f"System: {get_greeting()}")
    
    # 2. Use the marco_polo module
    test_phrases = ["marco", "Marco", "pizza", "polo"]
    
    print("\n--- Running Game Engine ---")
    for phrase in test_phrases:
        result = play_game(phrase)
        print(f"Input: '{phrase}' -> Output: {result}")

if __name__ == "__main__":  # pragma: no cover
    main()
