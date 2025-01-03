import os
import pytest
from app import app

@pytest.fixture(scope="session")
def client():
    """
    Provides a Flask test client for sending test requests to routes.

    This fixture sets up a Flask test client that can be used to 
    simulate HTTP requests to the Flask application for testing.

    Yields
    ------
    flask.testing.FlaskClient
        A Flask test client instance for sending requests to the app.
    """
    with app.test_client() as client:
        # Create the test client context
        yield client  # Provide the client to the test cases


@pytest.fixture
def mock_db_path(tmp_path):
    """
    Creates a mock SQLite database file in a temporary directory.

    This fixture generates an empty SQLite database file in a
    temporary directory. It can be optionally initialized with
    schema or data as needed by individual tests.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-provided fixture for creating temporary directories.

    Returns
    -------
    str
        Path to the mock SQLite database file as a string.
    """
    db_file = tmp_path / "test_patient_data.db"
    db_file.touch()  # Create an empty SQLite file
    return str(db_file)  # Return the file path as a string


@pytest.fixture
def example_config_file(tmp_path):
    """
    Creates a mock config file in JSON format for testing `load_config`.

    This fixture writes a sample JSON configuration file in a temporary 
    directory. It can be used to test functions that require loading 
    configuration files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-provided fixture for creating temporary directories.

    Returns
    -------
    str
        Path to the mock JSON configuration file as a string.
    """
    config_file_path = tmp_path / "test_config.json"
    # Write a simple key-value pair to the config file
    config_file_path.write_text('{"test_key": "test_value"}')
    return str(config_file_path)  # Return the file path as a string