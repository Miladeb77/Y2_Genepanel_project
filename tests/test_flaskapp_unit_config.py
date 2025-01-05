# tests_flaskapp/test_unit_config.py

import pytest
from app import load_config
import json

def test_load_config_valid(example_config_file):
    """
    Test that a valid JSON file is loaded correctly by the `load_config` function.

    This test ensures that when a valid JSON configuration file is passed to 
    the `load_config` function, it loads and returns the expected key-value pairs.

    Parameters
    ----------
    example_config_file : str
        Path to a valid JSON configuration file created by the `example_config_file` fixture.

    Asserts
    -------
    - The `test_key` key in the loaded configuration has the expected value.
    """
    # Act: Call load_config with the example config file
    config = load_config(example_config_file)
    
    # Assert: Verify the loaded configuration contains the expected key-value pair
    assert config["test_key"] == "test_value"


def test_load_config_file_not_found():
    """
    Test that `load_config` raises a FileNotFoundError if the file does not exist.

    This test ensures that when a non-existent file path is passed to the `load_config` 
    function, it raises the appropriate exception.

    Asserts
    -------
    - A `FileNotFoundError` is raised.
    """
    # Act & Assert: Ensure the function raises FileNotFoundError for a missing file
    with pytest.raises(FileNotFoundError):
        load_config("/non_existent_config.json")


def test_load_config_invalid_json(tmp_path):
    """
    Test that `load_config` raises a JSONDecodeError for invalid JSON content.

    This test ensures that when a file containing invalid JSON is passed to the 
    `load_config` function, it raises the appropriate exception.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-provided fixture for creating temporary directories.

    Asserts
    -------
    - A `JSONDecodeError` is raised when invalid JSON content is loaded.
    """
    # Arrange: Create a file with invalid JSON content
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{not valid JSON")  # Write malformed JSON content
    
    # Act & Assert: Ensure the function raises JSONDecodeError for invalid JSON
    with pytest.raises(json.JSONDecodeError):
        load_config(str(invalid_json_file))
