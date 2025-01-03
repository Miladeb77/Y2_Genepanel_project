import pytest
import logging
import os
from unittest.mock import patch, MagicMock
from PanelGeneMapper.modules.custom_logging import setup_logging


@pytest.fixture
def mock_os():
    """Mock `os.makedirs` and `os.path` functions."""
    with patch("os.makedirs") as mock_makedirs, patch("os.path.abspath", side_effect=lambda x: f"/mock_base_dir/{x}"), patch("os.path.join", side_effect=lambda *args: "/".join(args)), patch("os.path.dirname", return_value="/mock_base_dir"):
        yield mock_makedirs


@pytest.fixture
def mock_logging():
    """Mock the logging module."""
    with patch("logging.FileHandler") as mock_file_handler, patch("logging.StreamHandler") as mock_stream_handler, patch("logging.getLogger", return_value=logging.getLogger("test_logger")) as mock_get_logger:
        mock_file_handler.return_value = MagicMock()
        mock_stream_handler.return_value = MagicMock()
        yield mock_file_handler, mock_stream_handler, mock_get_logger




def test_setup_logging_failure(mock_os):
    """Test setup_logging raises an exception when logging fails."""
    with patch("os.makedirs", side_effect=Exception("Mocked exception")):
        with pytest.raises(RuntimeError, match="Failed to set up logging: Mocked exception"):
            setup_logging()
