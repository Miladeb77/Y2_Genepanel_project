import os
import pytest
import logging
import sqlite3
from unittest.mock import patch, MagicMock
from pathlib import Path
from PanelGeneMapper.generate_valid_rcode_list import main

###############################
# Fixtures
###############################

@pytest.fixture
def temp_root_dir(tmp_path):
    """
    Fixture to create a temporary root directory for functional tests.
    
    This root directory will simulate the environment in which the main function operates,
    including subdirectories for PanelApp, logs, and output.
    
    Returns
    -------
    pathlib.Path
        The path to the temporary root directory.
    """
    return tmp_path

@pytest.fixture
def mock_time_sleep(monkeypatch):
    """
    Fixture to mock time.sleep to prevent actual waiting during tests.
    
    This ensures that tests run quickly without delays introduced by sleep calls.
    """
    mock_sleep = MagicMock()
    monkeypatch.setattr("time.sleep", mock_sleep)
    return mock_sleep

@pytest.fixture
def mock_logging(monkeypatch):
    """
    Fixture to mock the logging module to capture log outputs without writing to files or console.
    
    This allows verification of logging behavior without side effects.
    """
    mock_log = MagicMock()
    monkeypatch.setattr(logging, 'getLogger', lambda: mock_log)
    monkeypatch.setattr(logging, 'info', mock_log.info)
    monkeypatch.setattr(logging, 'warning', mock_log.warning)
    monkeypatch.setattr(logging, 'error', mock_log.error)
    return mock_log

###############################
# Functional Tests
###############################

def test_full_process_with_new_database(temp_root_dir, mock_time_sleep, mock_logging):
    """
    Functional Test: Verify that the main process correctly handles a new PanelApp database.
    
    This test simulates the presence of a new PanelApp database file and ensures that the
    system processes it, extracts unique disorders, and saves them to the output file.
    
    Parameters
    ----------
    temp_root_dir : pathlib.Path
        Temporary root directory fixture.
    mock_time_sleep : MagicMock
        Mocked time.sleep to bypass actual delays.
    mock_logging : MagicMock
        Mocked logger to capture logging outputs.
    
    Asserts
    -------
    - Logs indicate successful processing.
    - The output file contains the expected unique disorders.
    """
    # Arrange: Create PanelApp directory with a new database file
    panelapp_dir = temp_root_dir / "panelapp"
    panelapp_dir.mkdir()
    db_file = panelapp_dir / "panelapp_v20240101.db"
    db_file.touch()

    # Create a SQLite database and populate it with relevant_disorders
    conn = sqlite3.connect(str(db_file))
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
        ("GeneB", "HGNC:67890", "R58", "2024-01-01"),
        ("GeneC", "HGNC:11111", "R46", "2024-01-01"),
    ])
    conn.commit()
    conn.close()

    # Patch 'root_dir' in the generate_valid_rcode_list module to point to temp_root_dir
    with patch('PanelGeneMapper.generate_valid_rcode_list.root_dir', str(temp_root_dir)):
        # Act: Run the main function once
        main()

    # Assert: Check that the output file contains the unique disorders
    output_dir = temp_root_dir / "generate_valid_rcodes_output"
    output_file = output_dir / "unique_relevant_disorders.txt"
    assert output_file.exists(), "Output file should be created."

    with open(output_file, "r") as f:
        disorders = f.read().splitlines()
    assert set(disorders) == {"R46", "R58"}, "Output file should contain the unique disorders R46 and R58."

    # Verify logging calls
    mock_logging.info.assert_any_call("Attempting to locate the PanelApp directory.")
    mock_logging.info.assert_any_call(f"PanelApp directory located at: {str(panelapp_dir)}")
    mock_logging.info.assert_any_call(f"Directories created or already exist: {os.path.join(temp_root_dir, 'logs')}, {str(output_dir)}")
    mock_logging.info.assert_any_call(f"Logging initialized. Log file: {os.path.join(temp_root_dir, 'logs', 'generate_valid_rcode_list.log')}")
    mock_logging.info.assert_any_call("Successfully processed new database and appended unique disorders.")

def test_full_process_with_existing_database(temp_root_dir, mock_time_sleep, mock_logging):
    """
    Functional Test: Ensure that re-processing an existing PanelApp database does not duplicate disorders.
    
    This test runs the main process twice with the same database file and verifies that the
    second run does not append duplicate disorders to the output file.
    
    Parameters
    ----------
    temp_root_dir : pathlib.Path
        Temporary root directory fixture.
    mock_time_sleep : MagicMock
        Mocked time.sleep to bypass actual delays.
    mock_logging : MagicMock
        Mocked logger to capture logging outputs.
    
    Asserts
    -------
    - The output file contains disorders only once.
    - Logs indicate that the database file was already processed.
    """
    # Arrange: Create PanelApp directory with a database file
    panelapp_dir = temp_root_dir / "panelapp"
    panelapp_dir.mkdir()
    db_file = panelapp_dir / "panelapp_v20240101.db"
    db_file.touch()

    # Create a SQLite database and populate it with relevant_disorders
    conn = sqlite3.connect(str(db_file))
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
        ("GeneB", "HGNC:67890", "R58", "2024-01-01"),
        ("GeneC", "HGNC:11111", "R46", "2024-01-01"),
    ])
    conn.commit()
    conn.close()

    # Patch 'root_dir' to point to temp_root_dir
    with patch('PanelGeneMapper.generate_valid_rcode_list.root_dir', str(temp_root_dir)):
        # Act: Run the main function twice
        main()
        main()

    # Assert: Check that the output file contains the unique disorders only once
    output_dir = temp_root_dir / "generate_valid_rcodes_output"
    output_file = output_dir / "unique_relevant_disorders.txt"
    assert output_file.exists(), "Output file should be created."

    with open(output_file, "r") as f:
        disorders = f.read().splitlines()
    assert set(disorders) == {"R46", "R58"}, "Output file should contain the unique disorders R46 and R58 without duplicates."

    # Verify logging calls indicating processing and duplication
    mock_logging.info.assert_any_call("Successfully processed new database and appended unique disorders.")
    mock_logging.info.assert_any_call("Database file already processed: panelapp_v20240101.db")

def test_full_process_no_new_disorders(temp_root_dir, mock_time_sleep, mock_logging):
    """
    Functional Test: Confirm that no changes occur when there are no new disorders to add.
    
    This test ensures that when the main process is run with existing disorders, the output
    file remains unchanged and no duplicates are introduced.
    
    Parameters
    ----------
    temp_root_dir : pathlib.Path
        Temporary root directory fixture.
    mock_time_sleep : MagicMock
        Mocked time.sleep to bypass actual delays.
    mock_logging : MagicMock
        Mocked logger to capture logging outputs.
    
    Asserts
    -------
    - The output file remains unchanged after processing.
    - Logs indicate that the database file was already processed.
    """
    # Arrange: Create PanelApp directory with a database file
    panelapp_dir = temp_root_dir / "panelapp"
    panelapp_dir.mkdir()
    db_file = panelapp_dir / "panelapp_v20240101.db"
    db_file.touch()

    # Create a SQLite database and populate it with relevant_disorders
    conn = sqlite3.connect(str(db_file))
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
        ("GeneB", "HGNC:67890", "R58", "2024-01-01"),
    ])
    conn.commit()
    conn.close()

    # Patch 'root_dir' to point to temp_root_dir
    with patch('PanelGeneMapper.generate_valid_rcode_list.root_dir', str(temp_root_dir)):
        # Act: Run the main function once to process the database
        main()

    # Modify the database without adding new disorders
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
        VALUES (?, ?, ?, ?)
    """, [
        ("GeneC", "HGNC:11111", "R46", "2024-01-01"),
    ])
    conn.commit()
    conn.close()

    # Act: Run the main function again
    with patch('PanelGeneMapper.generate_valid_rcode_list.root_dir', str(temp_root_dir)):
        main()

    # Assert: Check that the output file remains unchanged
    output_dir = temp_root_dir / "generate_valid_rcodes_output"
    output_file = output_dir / "unique_relevant_disorders.txt"
    assert output_file.exists(), "Output file should exist."

    with open(output_file, "r") as f:
        disorders = f.read().splitlines()
    expected_disorders = {"R46", "R58"}
    assert set(disorders) == expected_disorders, "No new disorders should be added to the output file."

    # Verify logging calls indicating that the database was already processed
    mock_logging.info.assert_any_call("Database file already processed: panelapp_v20240101.db")
