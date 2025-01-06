import pytest
import sqlite3
from unittest.mock import patch, MagicMock, call
from app import (
    extract_genes_and_metadata_from_panel,
    get_patient_data,
    add_patient_record,
)

def test_get_patient_data_empty_db(mock_db_path):
    """
    Test `get_patient_data` on an empty database.

    This test ensures that when the database is empty (i.e., the patient_data 
    table exists but contains no records), the function returns an empty list.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function returns an empty list.
    """
    # Arrange: Set up an empty patient_data table
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    conn.commit()
    conn.close()

    # Act: Call get_patient_data with a non-existing patient ID
    records = get_patient_data("Patient_123", mock_db_path)

    # Assert: Verify that the function returns an empty list
    assert records == [], "Expected an empty list from an empty patient_data table."


def test_get_patient_data_no_table(mock_db_path):
    """
    Test `get_patient_data` when the database has no `patient_data` table.

    This test ensures that if the `patient_data` table is missing from the 
    database, the function raises an `OperationalError`.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function raises an `OperationalError` due to the missing table.
    """
    # Act & Assert: Ensure the function raises an OperationalError
    with pytest.raises(sqlite3.OperationalError):
        get_patient_data("Patient_123", mock_db_path)


def test_get_patient_data_no_matching_records(mock_db_path):
    """
    Test `get_patient_data` when the database has records but none match the patient_id.

    This test ensures that when there are records in the database but none 
    match the given `patient_id`, the function returns an empty list.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function returns an empty list for a non-matching `patient_id`.
    """
    # Arrange: Set up a patient_data table with unrelated records
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO patient_data VALUES (?, ?, ?, ?)",
        ("Patient_999", "R46", "2024-12-25", "2024-12-24")
    )
    conn.commit()
    conn.close()

    # Act: Call get_patient_data with a non-matching patient ID
    records = get_patient_data("Patient_123", mock_db_path)

    # Assert: Verify that the function returns an empty list
    assert records == [], "Expected an empty list for non-matching patient_id."


def test_get_patient_data_single_record(mock_db_path):
    """
    Test `get_patient_data` with a single matching record in the database.

    This test ensures that when the database contains one record that matches 
    the given `patient_id`, the function returns a list containing that record.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function returns a list with one tuple containing the record data.
    """
    # Arrange: Set up a patient_data table with one matching record
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO patient_data VALUES (?, ?, ?, ?)",
        ("Patient_123", "R46", "2024-12-25", "2024-12-24")
    )
    conn.commit()
    conn.close()

    # Act: Call get_patient_data with a matching patient ID
    records = get_patient_data("Patient_123", mock_db_path)

    # Assert: Verify that the function returns the correct record
    assert len(records) == 1, "Expected one record."
    assert records[0] == ("Patient_123", "R46", "2024-12-25", "2024-12-24"), "Record does not match expected values."


def test_get_patient_data_multiple_records(mock_db_path):
    """
    Test `get_patient_data` with multiple matching records in the database.

    This test ensures that when the database contains multiple records matching 
    the given `patient_id`, the function returns all matching records as a list of tuples.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function returns a list with all matching records.
    """
    # Arrange: Set up a patient_data table with multiple matching records
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    cursor.executemany(
        "INSERT INTO patient_data VALUES (?, ?, ?, ?)",
        [
            ("Patient_123", "R46", "2024-12-25", "2024-12-24"),
            ("Patient_123", "R47", "2024-12-26", "2024-12-25")
        ]
    )
    conn.commit()
    conn.close()

    # Act: Call get_patient_data with a matching patient ID
    records = get_patient_data("Patient_123", mock_db_path)

    # Assert: Verify that the function returns all matching records
    assert len(records) == 2, "Expected two records."
    assert records == [
        ("Patient_123", "R46", "2024-12-25", "2024-12-24"),
        ("Patient_123", "R47", "2024-12-26", "2024-12-25")
    ], "Records do not match expected values."


def test_get_patient_data_sql_injection(mock_db_path):
    """
    Test `get_patient_data` with a patient_id that resembles an SQL injection attempt.

    This test ensures that the function is resistant to SQL injection attacks by
    verifying no unintended rows are returned or database changes occur.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The function returns an empty list for an SQL injection attempt.
    """
    # Arrange: Set up a patient_data table with some records
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    cursor.executemany(
        "INSERT INTO patient_data VALUES (?, ?, ?, ?)",
        [
            ("Patient_123", "R46", "2024-12-25", "2024-12-24"),
            ("Patient_999", "R47", "2024-12-26", "2024-12-25")
        ]
    )
    conn.commit()
    conn.close()

    # Act: Test the function with an SQL injection attempt
    records = get_patient_data("Patient_123'; DROP TABLE patient_data; --", mock_db_path)

    # Assert: Verify that no records are returned and no SQL injection occurred
    assert records == [], "Expected no records to be returned for SQL injection input."


def test_add_patient_record_new(mock_db_path):
    """
    Test `add_patient_record` inserts a new row into the `patient_data` table.

    This test creates the table manually, calls the function to add a record,
    and verifies that the record is correctly inserted into the database.

    Parameters
    ----------
    mock_db_path : str
        Path to the mock SQLite database provided by the `mock_db_path` fixture.

    Asserts
    -------
    - The `patient_data` table contains the new record with the correct values.
    """
    # Arrange: Set up the database with a patient_data table
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE patient_data (
            patient_id TEXT,
            clinical_id TEXT,
            test_date TEXT,
            panel_retrieved_date TEXT
        )
    """)
    conn.commit()
    conn.close()

    # Act: Call the function to add a new patient record
    add_patient_record(
        patient_id="Patient_001",
        r_code="R46",
        inserted_date="2024-12-25",
        panel_retrieved_date="2024-12-24",
        db_path=mock_db_path
    )

    # Assert: Verify the new record exists in the database
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_data")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    row = rows[0]
    assert row[0] == "Patient_001"
    assert row[1] == "R46"
    assert row[2] == "2024-12-25"
    assert row[3] == "2024-12-24"


@patch("app.os.path.exists", return_value=True)
@patch("app.os.remove")
@patch("app.decompress_if_needed", return_value="/fake/decompressed_path.db")
@patch("app.sqlite3.connect")
def test_extract_genes_and_metadata_from_panel_success(
    mock_connect,
    mock_decompress,
    mock_remove,
    mock_exists
):
    """
    Test extracting genes, HGNC IDs, and version metadata in a normal scenario,
    verifying ephemeral cleanup occurs, including removal of both the .db and .lock file.

    This test checks that when valid records exist in the database, the function
    returns correct gene/HGNC data and version metadata, and then removes both 
    the decompressed file and its .lock file if they exist.

    Parameters
    ----------
    mock_connect : unittest.mock.MagicMock
        Mock for sqlite3.connect simulating a successful database connection.
    mock_decompress : unittest.mock.MagicMock
        Mock for decompress_if_needed, returning a fake .db path.
    mock_remove : unittest.mock.MagicMock
        Mock for os.remove, used twice for .db and .lock.
    mock_exists : unittest.mock.MagicMock
        Mock for os.path.exists, set True so removal is triggered.

    Asserts
    -------
    - The function returns the expected gene list, HGNC list, and version.
    - os.remove(...) is called exactly twice: once for .db, once for .lock.
    - sqlite3.connect(...) is called with the decompressed path.
    """
    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("GeneA", "HGNC:12345"), ("GeneB", "HGNC:67890")]
    mock_cursor.fetchone.return_value = ("2024-11-19",)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    # Act
    genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel("/fake/path.db.gz", "R999")

    # Assert: data checks
    assert genes == ["GeneA", "GeneB"], "Expected gene list does not match."
    assert hgnc_ids == ["HGNC:12345", "HGNC:67890"], "Expected HGNC ID list does not match."
    assert version_created == "2024-11-19", "Expected version_created is incorrect."

    # Confirm ephemeral cleanup calls
    mock_decompress.assert_called_once()
    mock_connect.assert_called_once_with("/fake/decompressed_path.db")

    # Verify exactly 2 remove calls: .db + .lock
    mock_remove.assert_has_calls([
        call("/fake/decompressed_path.db"),
        call("/fake/decompressed_path.db.lock")
    ], any_order=True)
    assert mock_remove.call_count == 2, "Expected .db and .lock removal calls."

@patch("app.decompress_if_needed", side_effect=Exception("Decompression failed"))
def test_extract_genes_and_metadata_decompression_failure(mock_decompress):
    """
    Test `extract_genes_and_metadata_from_panel` when decompression fails.

    This test ensures that the function raises an exception if decompression
    fails during the process.

    Parameters
    ----------
    mock_decompress : unittest.mock.MagicMock
        Mocked `decompress_if_needed` function.

    Asserts
    -------
    - The function raises an exception with the expected message.
    - The decompression function is called once.
    """
    # Act & Assert: Verify the function raises an exception on decompression failure
    with pytest.raises(Exception, match="Decompression failed"):
        extract_genes_and_metadata_from_panel("/fake/path.db.gz", "R999")

    # Verify the decompression function was called
    mock_decompress.assert_called_once()

