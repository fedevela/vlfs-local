import os
from unittest.mock import patch

from main import main

def test_main():
    with patch("main.run_mcp") as mock_run_mcp:
        main()
        mock_run_mcp.assert_called_once()
