import sys
from pathlib import Path
from unittest.mock import patch

# Point to the new src/ directory
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import main

def test_main():
    with patch("builtins.print") as mock_print:
        main()
        
        # Verify print was called at least once
        assert mock_print.call_count > 0
        
        # Verify specific output
        calls = [call.args[0] for call in mock_print.call_args_list]
        assert "System: Hello from the isolated module!" in calls
        assert "\n--- Running Game Engine ---" in calls
        assert "Input: 'marco' -> Output: polo" in calls
