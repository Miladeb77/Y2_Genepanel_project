import pytest
import os
import sqlite3
import pandas as pd
import gzip
import tempfile
from PanelGeneMapper.modules.retrieve_gene_local_db import (
    get_databases_dir,
    get_archive_dir,
    retrieve_latest_panelapp_db,
    connect_and_join_databases,
)

@pytest.fixture
def setup_environment():
    """
    Set up a temporary environment for testing.
    """
    # Mock databases directory
    databases_dir = "databases"
    os.makedirs(databases_dir, exist_ok=True)

    # Mock archive directory
    archive_dir = os.path.join(databases_dir, "archive_databases")
    os.makedirs(archive_dir, exist_ok=True)

    # Mock output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    return {
        "databases_dir": str(databases_dir),
        "archive_dir": str(archive_dir),
        "output_dir": str(output_dir),
    }


def test_get_databases_dir():
    """
    Test that `get_databases_dir` returns the correct path and ensures the directory exists.
    """
    databases_dir = get_databases_dir()
    assert os.path.exists(databases_dir), "Databases directory was not created."
    assert databases_dir.endswith("databases")


def test_get_archive_dir():
    """
    Test that `get_archive_dir` returns the correct path and ensures the directory exists.
    """
    archive_dir = get_archive_dir()
    assert os.path.exists(archive_dir), "Archive directory was not created."
    assert archive_dir.endswith("archive_databases")


def retrieve_latest_panelapp_db(archive_folder=None, panelapp_db=None):
    """
    Retrieve the latest PanelApp database from the databases directory or archive folder.

    Args:
        archive_folder (str, optional): Path to the archive folder. If not provided, it uses the default.
        panelapp_db (str, optional): Specific PanelApp database file to use. If not provided, the latest is used.

    Returns:
        tuple: Path to the PanelApp database and a flag indicating if it's a temporary file.
    """
    try:
        databases_dir = get_databases_dir()
        archive_dir = get_archive_dir()

        if panelapp_db and os.path.isfile(panelapp_db):
            return panelapp_db, False

        # Check for the latest database in the databases directory
        db_files = [f for f in os.listdir(databases_dir) if f.startswith("panelapp_v") and f.endswith(".db")]
        if db_files:
            db_files.sort(reverse=True)  # Latest file based on name
            return os.path.join(databases_dir, db_files[0]), False

        # If no database found, check the archive folder
        if archive_dir:
            archived_files = [
                f for f in os.listdir(archive_dir) if f.startswith("panelapp_v") and f.endswith(".db.gz")
            ]
            if archived_files:
                archived_files.sort(reverse=True)
                latest_archived = archived_files[0]

                # Extract the latest archived file to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_file:
                    with gzip.open(os.path.join(archive_folder, latest_archived), 'rb') as f_in:
                        temp_file.write(f_in.read())
                    return temp_file.name, True

        raise FileNotFoundError("No PanelApp database found.")
    except Exception as e:
        print(f"An error occurred while retrieving the PanelApp database: {e}")
        raise
