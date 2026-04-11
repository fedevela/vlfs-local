from hello import get_greeting
from marco_polo import play_game

def main():
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
