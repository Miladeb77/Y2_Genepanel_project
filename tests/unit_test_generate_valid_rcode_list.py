import os
import pytest
import logging
import sqlite3
from unittest import mock
from unittest.mock import MagicMock, patch
from PanelGeneMapper.generate_valid_rcode_list import (
    setup_logging,
    find_panelapp_directory,
    process_panelapp_directory,
    get_unique_relevant_disorders,
    save_disorders_to_file,
)
from PanelGeneMapper.generate_valid_rcode_list import main

###############################
# Fixtures
###############################

# Define a global root_dir variable for testing
@pytest.fixture
def root_dir(tmp_path):
    """
    Fixture to provide a temporary root directory for testing.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    
    Returns
    -------
    str
        The path to the temporary root directory.
    """
    return str(tmp_path)

@pytest.fixture
def mock_logger(monkeypatch):
    """
    Fixture to mock the logging module.
    
    This fixture ensures that logging calls do not interfere with test outputs.
    """
    mock_log = MagicMock()
    monkeypatch.setattr(logging, 'getLogger', lambda: mock_log)
    return mock_log

###############################
# Unit Tests
###############################

def test_find_panelapp_directory_found(tmp_path):
    """
    Test that `find_panelapp_directory` successfully finds a directory containing a PanelApp database.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    
    Asserts
    -------
    - The function returns the correct subdirectory path containing the database file.
    """
    # Arrange: Create a subdirectory with a valid PanelApp database file
    subdir = tmp_path / "subdir_with_db"
    subdir.mkdir()
    db_file = subdir / "panelapp_v20240101.db"
    db_file.touch()
    
    # Act: Call find_panelapp_directory
    found_dir = find_panelapp_directory(str(tmp_path))
    
    # Assert: Verify the correct directory is returned
    assert found_dir == str(subdir), "Should return the subdirectory containing the PanelApp database"

def test_process_panelapp_directory_new_file(tmp_path, mock_logger):
    """
    Test that `process_panelapp_directory` correctly identifies and processes a new database file.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The function returns the correct database path and True flag.
    - The new database file is added to the processed versions file.
    """
    # Arrange: Create PanelApp directory and output directory
    panelapp_dir = tmp_path / "panelapp"
    panelapp_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create a new PanelApp database file
    db_file = panelapp_dir / "panelapp_v20240101.db"
    db_file.touch()
    
    # Act: Call process_panelapp_directory
    database_path, new_unprocessed_file_found = process_panelapp_directory(str(panelapp_dir), str(output_dir))
    
    # Assert: Verify correct return values
    assert database_path == str(db_file), "Should return the path to the new database file"
    assert new_unprocessed_file_found is True, "Should indicate that a new unprocessed file was found"
    
    # Verify that the processed file includes the new database file
    processed_file = output_dir / "processed_panelApp_versions.txt"
    with open(processed_file, "r") as f:
        processed_versions = f.read().splitlines()
    assert "panelapp_v20240101.db" in processed_versions, "Processed versions should include the new database file"

def test_process_panelapp_directory_existing_file(tmp_path, mock_logger):
    """
    Test that `process_panelapp_directory` does not process a database file that has already been processed.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The function returns None and False flag.
    """
    # Arrange: Create PanelApp directory and output directory
    panelapp_dir = tmp_path / "panelapp"
    panelapp_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create a processed_panelApp_versions.txt with an existing database file
    processed_file = output_dir / "processed_panelApp_versions.txt"
    with open(processed_file, "w") as f:
        f.write("panelapp_v20240101.db\n")
    
    # Create the same PanelApp database file
    db_file = panelapp_dir / "panelapp_v20240101.db"
    db_file.touch()
    
    # Act: Call process_panelapp_directory
    database_path, new_unprocessed_file_found = process_panelapp_directory(str(panelapp_dir), str(output_dir))
    
    # Assert: Verify correct return values
    assert database_path is None, "Should return None as the database file is already processed"
    assert new_unprocessed_file_found is False, "Should indicate that no new unprocessed file was found"

def test_get_unique_relevant_disorders_with_records(tmp_path):
    """
    Test that `get_unique_relevant_disorders` correctly retrieves unique disorders from the database.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    
    Asserts
    -------
    - The function returns a list of unique relevant disorders.
    """
    # Arrange: Create a SQLite database with the panel_info table and insert records
    db_path = tmp_path / "test_panelapp.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE panel_info (
            gene_symbol TEXT NOT NULL,
            hgnc_id TEXT NOT NULL,
            relevant_disorders TEXT NOT NULL,
            version_created TEXT NOT NULL
        )
    """)
    cursor.executemany("""
        INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
        VALUES (?, ?, ?, ?)
    """, [
        ("GeneA", "HGNC:12345", "R46", "2024-01-01"),
        ("GeneB", "HGNC:67890", "R46", "2024-01-01"),
        ("GeneC", "HGNC:11111", "R58", "2024-01-02"),
    ])
    conn.commit()
    conn.close()
    
    # Act: Call get_unique_relevant_disorders
    unique_disorders = get_unique_relevant_disorders(str(db_path))
    
    # Assert: Verify the unique disorders list
    assert unique_disorders == ["R46", "R58"], "Should return all unique relevant disorders"

def test_get_unique_relevant_disorders_empty_table(tmp_path):
    """
    Test that `get_unique_relevant_disorders` returns an empty list when the table is empty.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    
    Asserts
    -------
    - The function returns an empty list.
    """
    # Arrange: Create a SQLite database with an empty panel_info table
    db_path = tmp_path / "empty_panelapp.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE panel_info (
            gene_symbol TEXT NOT NULL,
            hgnc_id TEXT NOT NULL,
            relevant_disorders TEXT NOT NULL,
            version_created TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    
    # Act: Call get_unique_relevant_disorders
    unique_disorders = get_unique_relevant_disorders(str(db_path))
    
    # Assert: Verify the unique disorders list is empty
    assert unique_disorders == [], "Should return an empty list when the table has no records"

def test_save_disorders_to_file_new_disorders(tmp_path, mock_logger):
    """
    Test that `save_disorders_to_file` correctly appends new disorders to an empty file.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The output file contains the new disorders.
    """
    # Arrange: Define disorders and output file path
    disorders = ["Disorder_1", "Disorder_2"]
    output_file = tmp_path / "disorders.txt"
    
    # Act: Call save_disorders_to_file
    save_disorders_to_file(disorders, str(output_file))
    
    # Assert: Verify that the disorders are written to the file
    with open(output_file, "r") as f:
        lines = f.read().splitlines()
    assert lines == disorders, "Output file should contain the new disorders"

def test_save_disorders_to_file_existing_disorders(tmp_path, mock_logger):
    """
    Test that `save_disorders_to_file` appends only new disorders and avoids duplicates.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - Only new disorders are appended to the file.
    """
    # Arrange: Pre-populate the output file with existing disorders
    existing_disorders = ["Disorder_1", "Disorder_2"]
    output_file = tmp_path / "disorders.txt"
    with open(output_file, "w") as f:
        for disorder in existing_disorders:
            f.write(f"{disorder}\n")
    
    # Define new disorders, some of which are duplicates
    new_disorders = ["Disorder_2", "Disorder_3", "Disorder_4"]
    
    # Act: Call save_disorders_to_file
    save_disorders_to_file(new_disorders, str(output_file))
    
    # Assert: Verify that only new disorders are appended
    with open(output_file, "r") as f:
        lines = f.read().splitlines()
    expected_disorders = ["Disorder_1", "Disorder_2", "Disorder_3", "Disorder_4"]
    assert lines == expected_disorders, "Only new disorders should be appended to the file"

def test_save_disorders_to_file_no_new_disorders(tmp_path, mock_logger):
    """
    Test that `save_disorders_to_file` does not modify the file when there are no new disorders.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The output file remains unchanged when no new disorders are provided.
    """
    # Arrange: Pre-populate the output file with existing disorders
    existing_disorders = ["Disorder_1", "Disorder_2"]
    output_file = tmp_path / "disorders.txt"
    with open(output_file, "w") as f:
        for disorder in existing_disorders:
            f.write(f"{disorder}\n")
    
    # Define new disorders that are all duplicates
    new_disorders = ["Disorder_1", "Disorder_2"]
    
    # Act: Call save_disorders_to_file
    save_disorders_to_file(new_disorders, str(output_file))
    
    # Assert: Verify that the file remains unchanged
    with open(output_file, "r") as f:
        lines = f.read().splitlines()
    assert lines == existing_disorders, "File should remain unchanged when no new disorders are provided"

def test_save_disorders_to_file_create_new_file(tmp_path, mock_logger):
    """
    Test that `save_disorders_to_file` creates a new file if it does not exist.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The output file is created and contains the new disorders.
    """
    # Arrange: Define disorders and output file path (file does not exist)
    disorders = ["Disorder_1", "Disorder_2"]
    output_file = tmp_path / "new_disorders.txt"
    
    # Act: Call save_disorders_to_file
    save_disorders_to_file(disorders, str(output_file))
    
    # Assert: Verify that the file is created and contains the disorders
    assert output_file.exists(), "Output file should be created if it does not exist"
    with open(output_file, "r") as f:
        lines = f.read().splitlines()
    assert lines == disorders, "Output file should contain the new disorders"

def test_save_disorders_to_file_empty_disorders(tmp_path, mock_logger):
    """
    Test that `save_disorders_to_file` does not modify the file when disorders list is empty.
    
    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.
    mock_logger : MagicMock
        Mocked logger to verify informational logs.
    
    Asserts
    -------
    - The output file remains unchanged when the disorders list is empty.
    """
    # Arrange: Pre-populate the output file with existing disorders
    existing_disorders = ["Disorder_1", "Disorder_2"]
    output_file = tmp_path / "disorders.txt"
    with open(output_file, "w") as f:
        for disorder in existing_disorders:
            f.write(f"{disorder}\n")
    
    # Define an empty disorders list
    new_disorders = []
    
    # Act: Call save_disorders_to_file
    save_disorders_to_file(new_disorders, str(output_file))
    
    # Assert: Verify that the file remains unchanged
    with open(output_file, "r") as f:
        lines = f.read().splitlines()
    assert lines == existing_disorders, "File should remain unchanged when disorders list is empty"

