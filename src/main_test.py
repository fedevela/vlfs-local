import os
import sys
import pytest
from unittest.mock import patch

from main import main

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key", "VLFS_ROOT_DIR": "/fake/dir"})
def test_main_success():
    with patch("main.run_mcp") as mock_run_mcp:
        main()
        mock_run_mcp.assert_called_once()

@patch.dict(os.environ, {"LOCAL_DEV_MODE": "true", "VLFS_ROOT_DIR": "/fake/dir"})
def test_main_local_dev_mode_success():
    with patch("main.run_mcp") as mock_run_mcp:
        main()
        mock_run_mcp.assert_called_once()

@patch.dict(os.environ, {}, clear=True)
def test_main_missing_env(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Error: Missing required environment variables: GEMINI_API_KEY, VLFS_ROOT_DIR" in captured.out

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}, clear=True)
def test_main_missing_one_env(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Error: Missing required environment variables: VLFS_ROOT_DIR" in captured.out
