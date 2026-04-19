import os
import pytest
from unittest.mock import patch

from main import main

def test_main_success():
    with patch("main.run_mcp") as mock_run_mcp:
        main()
        mock_run_mcp.assert_called_once()
