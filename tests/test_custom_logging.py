import logging
import os
from unittest.mock import patch, MagicMock

import pytest

from PanelGeneMapper.modules.custom_logging import setup_logging


@pytest.fixture
def mock_os():
    """
    Fixture to mock `os` functions such as `os.makedirs`, `os.path.abspath`,
    `os.path.join`, and `os.path.dirname`. This ensures tests run in isolation
    without affecting or depending on the actual file system.
    """
    with patch("os.makedirs") as mock_makedirs, \
         patch("os.path.abspath", side_effect=lambda x: f"/mock_base_dir/{x}"), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)), \
         patch("os.path.dirname", return_value="/mock_base_dir"):
        # Yield the mocked `os.makedirs` function to test cases.
        yield mock_makedirs

@pytest.fixture
def mock_logging():
    """
    Fixture to mock the `logging` module components, including `FileHandler`, 
    `StreamHandler`, and `getLogger`. This avoids actual file or console 
    logging during tests and provides a controlled environment for logging behavior.
    """
    with patch("logging.FileHandler") as mock_file_handler, \
         patch("logging.StreamHandler") as mock_stream_handler, \
         patch("logging.getLogger", return_value=logging.getLogger("test_logger")) as mock_get_logger:
        # Create mock return values for handlers.
        mock_file_handler.return_value = MagicMock()
        mock_stream_handler.return_value = MagicMock()
        # Yield the mocked components to test cases.
        yield mock_file_handler, mock_stream_handler, mock_get_logger

def test_setup_logging_failure(mock_os):
    """
    Test that `setup_logging` raises a RuntimeError when an exception occurs 
    while creating the logging directories.
    
    Args:
        mock_os: The mocked `os` functions to simulate an exception during 
                 directory creation.
    """
    # Simulate an exception during `os.makedirs` call.
    with patch("os.makedirs", side_effect=Exception("Mocked exception")):
        # Verify that `setup_logging` raises a RuntimeError with the expected message.
        with pytest.raises(RuntimeError, match="Failed to set up logging: Mocked exception"):
            setup_logging()
