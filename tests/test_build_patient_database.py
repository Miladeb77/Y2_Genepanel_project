import os
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

from PanelGeneMapper.modules.build_patient_database import (
    load_patient_data,
    generate_patient_database,
    save_to_database,
)


# Mock data for tests
MOCK_PATIENT_JSON = [
    {"patient_id": "Patient_1", "clinical_id": "R169", "test_date": "2023-12-20"},
    {"patient_id": "Patient_2", "clinical_id": "R419", "test_date": "2023-11-15"},
]

MOCK_GENERATED_DATA = pd.DataFrame({
    # Mock data representing a patient database for testing.
    "patient_id": ["Patient_1", "Patient_2"],  # Unique identifiers for patients.
    "clinical_id": ["R169", "R419"],  # Clinical identifiers for patients.
    "test_date": ["2023-12-20", "2023-11-15"],  # Dates when tests were conducted.
    "panel_retrieved_date": [datetime.now().strftime("%Y-%m-%d")] * 2  # Current date as the retrieval date.
})

@pytest.fixture
def mock_os():
    """Fixture to mock os operations."""
    # Mock `os.path.exists` and `os.makedirs` to avoid real file system changes.
    with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
        mock_exists.return_value = True  # Simulate that the path always exists.
        yield mock_exists, mock_makedirs  # Yield mocked methods for use in tests.

@pytest.fixture
def mock_json():
    """Fixture to mock JSON file reading."""
    # Mock the `open` function and `pandas.read_json` to simulate reading a JSON file.
    with patch("builtins.open", MagicMock()) as mock_open, patch("pandas.read_json") as mock_read_json:
        mock_read_json.return_value = pd.DataFrame(MOCK_PATIENT_JSON)  # Mocked DataFrame for patient data.
        yield mock_open, mock_read_json  # Yield mocked methods for use in tests.

@pytest.fixture
def mock_sqlite():
    """Fixture to mock SQLite database connection."""
    # Mock the `sqlite3.connect` function to simulate database operations.
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()  # Mocked connection object.
        mock_conn.__enter__.return_value = mock_conn  # Support context manager protocol.
        yield mock_connect  # Yield mocked connect method for use in tests.

def test_load_patient_data(mock_os, mock_json):
    """Test loading patient data from a JSON file."""
    # Define mock directories and file paths for the test.
    databases_dir = "mock_databases"
    patient_data_file = "patients.json"

    # Call the function under test with mock paths.
    data = load_patient_data(databases_dir, patient_data_file)

    # Verify that the returned data matches the mocked JSON data.
    assert data == MOCK_PATIENT_JSON

def test_generate_patient_database_with_provided_data():
    """Test generating a patient database with user-provided data."""
    # Call the function with mocked patient data.
    df = generate_patient_database(num_patients=0, patient_data=MOCK_PATIENT_JSON)

    # Verify that the generated DataFrame matches the mock data exactly.
    pd.testing.assert_frame_equal(df, MOCK_GENERATED_DATA)

def test_generate_patient_database_without_provided_data():
    """Test generating a patient database without user-provided data."""
    # Specify the number of patients to generate.
    num_patients = 2

    # Call the function to generate the DataFrame.
    df = generate_patient_database(num_patients=num_patients, patient_data=None)

    # Verify the DataFrame structure and size.
    assert len(df) == num_patients  # Check the number of generated patients.
    assert "patient_id" in df.columns  # Verify `patient_id` column exists.
    assert "clinical_id" in df.columns  # Verify `clinical_id` column exists.
    assert "test_date" in df.columns  # Verify `test_date` column exists.
    assert "panel_retrieved_date" in df.columns  # Verify `panel_retrieved_date` column exists.


