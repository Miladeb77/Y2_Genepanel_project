import os
import shutil
import sqlite3

import pytest

from PanelGeneMapper.modules.make_bed_file import (
    create_local_db,
    cache_exon_data,
    fetch_cached_data,
    extract_ensembl_ids_from_csv,
    get_mane_exon_data,
    write_bed_file,
    fetch_all_data,
)

@pytest.fixture(scope="function")
def mock_database():
    """
    Create a mock SQLite database with the `gene_exons` table for testing.
    Cleans up after each test.
    """
    # Create a temporary database file
    mock_db_path = "test_gene_data.db"

    # Connect to the mock database and create the `gene_exons` table
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gene_exons (
            gene_id TEXT PRIMARY KEY,
            exon_data TEXT
        )
        """
    )
    # Insert mock data if needed
    cursor.execute(
        """
        INSERT INTO gene_exons (gene_id, exon_data) VALUES 
        ('ENSG00000128973', '{"exons": []}'),
        ('ENSG00000136827', '{"exons": []}')
        """
    )
    conn.commit()
    conn.close()

    yield mock_db_path

    # Cleanup after test
    if os.path.exists(mock_db_path):
        os.remove(mock_db_path)

@pytest.fixture(scope="function")
def cleanup_environment():
    """
    Fixture to clean up files and directories created during tests.
    """
    yield
    # Cleanup local files
    cleanup_test_files()

def cleanup_test_files():
    """
    Remove test files and directories created during testing.
    Handles `gene_exons.bed` in the current directory and `gene_data.bed` in the `output` directory.
    """
    # Current directory cleanup
    current_dir_files = ["gene_exons.bed"]
    for file in current_dir_files:
        if os.path.exists(file):
            os.remove(file)

    # Cleanup `gene_data.bed` in the `output` directory
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith(".bed"):
                os.remove(os.path.join(output_dir, file))

# def test_get_mane_exon_data_success(mock_database):
#     """
#     Test that the get_mane_exon_data function returns an expected dictionary 
#     output when provided with valid inputs.
#     """
#     species = "homo_sapiens"
#     server = "https://rest.ensembl.org"
#     headers = {"Content-Type": "application/json"}
#     ensembl_id = "ENSG00000012048"

#     result = get_mane_exon_data(ensembl_id, species, server, headers)
#     assert type(result) == dict

# def test_get_mane_exon_data_fail(mock_database):
#     """
#     Test that the get_mane_exon_data function returns None when an invalid input is provided.
#     """
#     species = "test"
#     server = "https://rest.ensembl.org"
#     headers = {"Content-Type": "application/json"}
#     ensembl_id = "ENSG00000012048"

#     result = get_mane_exon_data(ensembl_id, species, server, headers)
#     assert result is None

def test_write_bed_file_success(mock_database):
    """
    Test that the write_bed_file function creates the expected output file when provided with valid inputs.
    """
    data_list = ['ENSG00000128973', 'ENSG00000136827', 'ENSG00000064601', 'ENSG00000144381', 'ENSG00000143469']
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
    output_file = os.path.join(output_dir, 'gene_exons.bed')

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    result = write_bed_file(data_list, output_file)
    assert os.path.exists(output_file)
