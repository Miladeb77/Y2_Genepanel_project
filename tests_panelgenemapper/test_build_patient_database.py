import pytest
import pandas as pd
import os
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime
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
    "patient_id": ["Patient_1", "Patient_2"],
    "clinical_id": ["R169", "R419"],
    "test_date": ["2023-12-20", "2023-11-15"],
    "panel_retrieved_date": [datetime.now().strftime("%Y-%m-%d")] * 2
})


@pytest.fixture
def mock_os():
    """Fixture to mock os operations."""
    with patch("os.path.exists") as mock_exists, patch("os.makedirs") as mock_makedirs:
        mock_exists.return_value = True
        yield mock_exists, mock_makedirs


@pytest.fixture
def mock_json():
    """Fixture to mock JSON file reading."""
    with patch("builtins.open", MagicMock()) as mock_open, patch("pandas.read_json") as mock_read_json:
        mock_read_json.return_value = pd.DataFrame(MOCK_PATIENT_JSON)
        yield mock_open, mock_read_json


@pytest.fixture
def mock_sqlite():
    """Fixture to mock SQLite database connection."""
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        yield mock_connect


def test_load_patient_data(mock_os, mock_json):
    """Test loading patient data from a JSON file."""
    databases_dir = "mock_databases"
    patient_data_file = "patients.json"

    data = load_patient_data(databases_dir, patient_data_file)

    assert data == MOCK_PATIENT_JSON


def test_generate_patient_database_with_provided_data():
    """Test generating a patient database with user-provided data."""
    df = generate_patient_database(num_patients=0, patient_data=MOCK_PATIENT_JSON)

    pd.testing.assert_frame_equal(df, MOCK_GENERATED_DATA)


def test_generate_patient_database_without_provided_data():
    """Test generating a patient database without user-provided data."""
    num_patients = 2
    df = generate_patient_database(num_patients=num_patients, patient_data=None)

    assert len(df) == num_patients
    assert "patient_id" in df.columns
    assert "clinical_id" in df.columns
    assert "test_date" in df.columns
    assert "panel_retrieved_date" in df.columns


