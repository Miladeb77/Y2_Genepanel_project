import os
import sqlite3
from unittest import mock

import pandas as pd
import pytest

from PanelGeneMapper.modules.patient_db_lookup_add import (
    get_databases_dir,
    list_patients,
    add_patient,
    save_to_database,
)


@pytest.fixture
def mock_database_dir(tmp_path):
    """Fixture to create a temporary directory as mock database directory."""
    # Create a temporary directory for mock database files using pytest's tmp_path.
    mock_dir = tmp_path / "databases"
    mock_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory is created.
    return mock_dir  # Return the created directory for use in tests.

def test_get_databases_dir(mock_database_dir, monkeypatch):
    """Test that `get_databases_dir` creates the correct directory."""
    # Monkeypatch `os.path.abspath` to return the mock directory path.
    monkeypatch.setattr("os.path.abspath", lambda x: str(mock_database_dir))
    result = get_databases_dir()  # Call the function under test.
    # Verify the directory exists.
    assert os.path.exists(result)
    # Verify the directory's name matches the expected name.
    assert os.path.basename(result) == "databases"

@mock.patch("sqlite3.connect")
@mock.patch("os.path.isfile")
@mock.patch("pandas.read_sql_query")
def test_list_patients(mock_read_sql, mock_isfile, mock_connect, tmp_path):
    """Test the `list_patients` function."""
    # Setup: Mock the responses of dependent functions.
    mock_isfile.return_value = True  # Mock that the database file exists.
    mock_conn = mock.MagicMock()  # Mock a database connection object.
    mock_connect.return_value = mock_conn  # Return the mocked connection.
    # Mock a DataFrame to simulate the query results.
    mock_df = pd.DataFrame({"patient_id": ["123"], "clinical_id": ["456"]})
    mock_read_sql.return_value = mock_df  # Set the mocked return value for SQL query.

    # Execute the function under test.
    result = list_patients(patient_db="test.db", save_to_file=False)

    # Verify: Ensure the mocked methods were called as expected.
    mock_isfile.assert_called_once()  # Verify `os.path.isfile` was called.
    mock_connect.assert_called_once()  # Verify the database connection was opened.
    mock_read_sql.assert_called_once()  # Verify the SQL query was executed.
    # Ensure the function's output matches the mocked DataFrame.
    assert mock_df.equals(mock_read_sql.return_value)

@mock.patch("sqlite3.connect")
@mock.patch("os.listdir")
@mock.patch("pandas.read_sql_query")
def test_add_patient(mock_read_sql, mock_listdir, mock_connect, tmp_path):
    """Test the `add_patient` function."""
    # Setup: Mock the responses of dependent functions.
    mock_listdir.return_value = ["panelapp_v20220101.db"]  # Simulate database files in the directory.
    mock_conn = mock.MagicMock()  # Mock a database connection object.
    mock_connect.return_value = mock_conn  # Return the mocked connection.
    # Mock a DataFrame to simulate existing patients in the database.
    mock_read_sql.return_value = pd.DataFrame({"patient_id": ["123"]})

    # Execute the function under test with a mock for the `to_sql` method.
    with mock.patch("pandas.DataFrame.to_sql") as mock_to_sql:
        add_patient("456", "789", "2023-12-31")  # Call the function to add a patient.
        mock_to_sql.assert_called_once()  # Verify the patient data was written to the database.

    # Verify: Ensure the mocked methods were called as expected.
    mock_read_sql.assert_called_once()  # Verify the SQL query for existing patients was executed.
    mock_listdir.assert_called_once()  # Verify the directory listing was checked.
