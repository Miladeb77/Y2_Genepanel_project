import pytest
import os
import sqlite3
import pandas as pd
from unittest import mock
from PanelGeneMapper.modules.patient_db_lookup_add import (
    get_databases_dir,
    list_patients,
    add_patient,
    save_to_database,
)

@pytest.fixture
def mock_database_dir(tmp_path):
    """Fixture to create a temporary directory as mock database directory."""
    mock_dir = tmp_path / "databases"
    mock_dir.mkdir(parents=True, exist_ok=True)
    return mock_dir

def test_get_databases_dir(mock_database_dir, monkeypatch):
    """Test that `get_databases_dir` creates the correct directory."""
    monkeypatch.setattr("os.path.abspath", lambda x: str(mock_database_dir))
    result = get_databases_dir()
    assert os.path.exists(result)
    assert os.path.basename(result) == "databases"

@mock.patch("sqlite3.connect")
@mock.patch("os.path.isfile")
@mock.patch("pandas.read_sql_query")
def test_list_patients(mock_read_sql, mock_isfile, mock_connect, tmp_path):
    """Test the `list_patients` function."""
    # Setup
    mock_isfile.return_value = True
    mock_conn = mock.MagicMock()
    mock_connect.return_value = mock_conn
    mock_df = pd.DataFrame({"patient_id": ["123"], "clinical_id": ["456"]})
    mock_read_sql.return_value = mock_df

    # Execute
    result = list_patients(patient_db="test.db", save_to_file=False)

    # Verify
    mock_isfile.assert_called_once()
    mock_connect.assert_called_once()
    mock_read_sql.assert_called_once()
    assert mock_df.equals(mock_read_sql.return_value)

@mock.patch("sqlite3.connect")
@mock.patch("os.listdir")
@mock.patch("pandas.read_sql_query")
def test_add_patient(mock_read_sql, mock_listdir, mock_connect, tmp_path):
    """Test the `add_patient` function."""
    # Setup
    mock_listdir.return_value = ["panelapp_v20220101.db"]
    mock_conn = mock.MagicMock()
    mock_connect.return_value = mock_conn
    mock_read_sql.return_value = pd.DataFrame({"patient_id": ["123"]})  # Mock existing patients

    # Execute
    with mock.patch("pandas.DataFrame.to_sql") as mock_to_sql:
        add_patient("456", "789", "2023-12-31")
        mock_to_sql.assert_called_once()

    # Verify
    mock_read_sql.assert_called_once()
    mock_listdir.assert_called_once()

