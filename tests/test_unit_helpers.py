# tests_flaskapp/test_unit_helpers.py

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from app import (
    decompress_if_needed,
    find_relevant_panel_db,
    find_most_recent_panel_db,
    find_most_recent_panel_date,
)

def test_decompress_if_needed_no_gz(tmp_path):
    """
    Test `decompress_if_needed` with a file that is not a `.gz` file.

    This test ensures that the function returns the same file path without any changes
    if the input file does not have a `.gz` extension.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The returned file path is identical to the input file path.
    """
    # Arrange: Create a test file without a .gz extension
    file_path = tmp_path / "test_file.db"
    file_path.touch()  # Create an empty file

    # Act: Call decompress_if_needed
    result = decompress_if_needed(str(file_path))

    # Assert: Verify that the original file path is returned
    assert result == str(file_path), "Should return original path if not .gz"


@patch("app.FileLock")
@patch("app.shutil.copyfileobj")
@patch("app.gzip.open")
@patch("app.os.path.getsize", return_value=100)  # Mock non-empty file size
def test_decompress_if_needed_gz(
    mock_getsize, mock_gzip_open, mock_shutil_copy, mock_filelock, tmp_path
):
    """
    Test `decompress_if_needed` with a `.gz` file.

    This test ensures that the function correctly decompresses `.gz` files and returns
    the path to the decompressed file.

    Parameters
    ----------
    mock_getsize : unittest.mock.MagicMock
        Mocked `os.path.getsize` function to simulate non-empty files.
    mock_gzip_open : unittest.mock.MagicMock
        Mocked `gzip.open` function to simulate gzip file opening.
    mock_shutil_copy : unittest.mock.MagicMock
        Mocked `shutil.copyfileobj` function to simulate file copying.
    mock_filelock : unittest.mock.MagicMock
        Mocked `FileLock` function to simulate file locking.
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The returned file path ends with `.db`.
    - The `gzip.open` and `shutil.copyfileobj` functions are called exactly once.
    """
    # Arrange: Create an empty .gz file
    gz_path = tmp_path / "test_file.db.gz"
    gz_path.touch()

    # Act: Call decompress_if_needed
    result_path = decompress_if_needed(str(gz_path))

    # Assert: Verify that the decompressed file path ends with `.db`
    assert result_path.endswith(".db"), "Decompressed file path should end with .db"

    # Verify that the mocked functions are called
    mock_gzip_open.assert_called_once()
    mock_shutil_copy.assert_called_once()


def test_find_relevant_panel_db_found(tmp_path):
    """
    Test `find_relevant_panel_db` when a matching panel database is found.

    This test ensures that the function correctly locates a panel database file
    matching a specific date in the format `YYYY-MM-DD`.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The returned file path contains the correct date prefix.
    """
    # Arrange: Create a file with a name matching the expected prefix
    panel_date = "2024-11-19"
    prefix = "panelapp_v20241119"
    db_file = tmp_path / f"{prefix}.db"
    db_file.touch()  # Create the file

    # Act: Call find_relevant_panel_db
    found_db = find_relevant_panel_db(panel_date, str(tmp_path))

    # Assert: Verify that the returned file path matches the prefix
    assert prefix in found_db, "Should find the file matching panel date"


def test_find_relevant_panel_db_not_found(tmp_path):
    """
    Test `find_relevant_panel_db` when no matching panel database is found.

    This test ensures that the function raises a `FileNotFoundError` if no
    database file matches the specified date.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function raises a `FileNotFoundError`.
    """
    # Act & Assert: Call find_relevant_panel_db and expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        find_relevant_panel_db("2024-11-19", str(tmp_path))


def test_find_most_recent_panel_db_no_files(tmp_path):
    """
    Test `find_most_recent_panel_db` when there are no valid `.db` files.

    This test ensures that the function raises a `FileNotFoundError` if there
    are no files with a `.db` extension in the directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function raises a `FileNotFoundError` with the expected message.
    """
    # Act & Assert: Call find_most_recent_panel_db and expect a FileNotFoundError
    with pytest.raises(FileNotFoundError, match="No uncompressed PanelApp database found."):
        find_most_recent_panel_db(str(tmp_path))


def test_find_most_recent_panel_db_only_non_matching_files(tmp_path):
    """
    Test `find_most_recent_panel_db` when only non-matching files are present.

    This test ensures that the function raises a `FileNotFoundError` if there
    are no valid files with the `panelapp_v*.db` naming convention in the directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function raises a `FileNotFoundError`.
    """
    # Arrange: Create a file that does not match the expected naming convention
    non_matching = tmp_path / "some_other_file.db"
    non_matching.touch()  # Create the file

    # Act & Assert: Call find_most_recent_panel_db and expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        find_most_recent_panel_db(str(tmp_path))


def test_find_most_recent_panel_db_one_valid_file(tmp_path):
    """
    Test `find_most_recent_panel_db` with exactly one valid .db file.

    This test ensures that the function correctly identifies and returns the only
    valid database file in the directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function returns the path to the single valid database file.
    """
    # Arrange: Create a single valid database file
    valid_db = tmp_path / "panelapp_v20231201.db"
    valid_db.touch()

    # Act: Call find_most_recent_panel_db
    result = find_most_recent_panel_db(str(tmp_path))

    # Assert: Verify that the single valid file is returned
    assert str(valid_db) == result, "Should find the single valid file present."


def test_find_most_recent_panel_db_newer_file(tmp_path):
    """
    Test `find_most_recent_panel_db` with multiple valid files.

    This test ensures that when multiple valid `.db` files exist, the function
    returns the file with the most recent creation time.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function returns the path to the newest database file based on creation time.
    """
    # Arrange: Create two database files with different creation times
    old_db = tmp_path / "panelapp_v20230101.db"
    new_db = tmp_path / "panelapp_v20240101.db"
    old_db.touch()
    time.sleep(0.01)  # Ensure different creation times
    new_db.touch()

    # Act: Call find_most_recent_panel_db
    result = find_most_recent_panel_db(str(tmp_path))

    # Assert: Verify that the newer file is returned
    assert str(new_db) == result, "Should pick the newer DB based on ctime."


def test_find_most_recent_panel_db_ignores_gz(tmp_path):
    """
    Test `find_most_recent_panel_db` ignores `.gz` files.

    This test ensures that compressed `.gz` files are not considered valid
    uncompressed database files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function raises a `FileNotFoundError` if only `.gz` files are present.
    """
    # Arrange: Create a compressed `.gz` file
    gz_file = tmp_path / "panelapp_v20241201.db.gz"
    gz_file.touch()

    # Act & Assert: Call find_most_recent_panel_db and expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        find_most_recent_panel_db(str(tmp_path))


def test_find_most_recent_panel_db_ignores_archive_directory(tmp_path):
    """
    Test `find_most_recent_panel_db` ignores files in `archive_databases`.

    This test ensures that the function skips over files located in directories
    named `archive_databases`.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function returns the most recent valid file outside the `archive_databases` directory.
    """
    # Arrange: Create an archive directory and valid files
    archive_dir = tmp_path / "archive_databases"
    archive_dir.mkdir()

    archived_file = archive_dir / "panelapp_v20241201.db"
    archived_file.touch()

    valid_file = tmp_path / "panelapp_v20241130.db"
    valid_file.touch()

    # Act: Call find_most_recent_panel_db
    result = find_most_recent_panel_db(str(tmp_path))

    # Assert: Verify that the file outside the archive directory is returned
    assert str(valid_file) == result, (
        "Should ignore files in 'archive_databases' directory "
        "and return the unarchived valid file."
    )


def test_find_most_recent_panel_db_multiple_subdirs(tmp_path):
    """
    Test `find_most_recent_panel_db` traverses subdirectories.

    This test ensures that the function searches through subdirectories
    and picks the newest valid file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function returns the newest valid database file across subdirectories.
    """
    # Arrange: Create subdirectories and valid files
    sub1 = tmp_path / "subdir1"
    sub2 = tmp_path / "subdir2"
    sub1.mkdir()
    sub2.mkdir()

    db1 = sub1 / "panelapp_v20240101.db"
    db2 = sub2 / "panelapp_v20250101.db"  # Newest file
    db1.touch()
    time.sleep(0.01)
    db2.touch()

    # Act: Call find_most_recent_panel_db
    result = find_most_recent_panel_db(str(tmp_path))

    # Assert: Verify that the newest file is returned
    assert str(db2) == result, "Should traverse subdirs and pick the newest valid DB."


def test_find_most_recent_panel_db_same_ctime(tmp_path):
    """
    Test `find_most_recent_panel_db` with files having the same creation time.

    This test ensures that the function handles multiple files with the same
    creation time gracefully and returns one of them without errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The function returns one of the files with the same creation time.
    """
    # Arrange: Create two valid files with the same creation time
    db1 = tmp_path / "panelapp_v20230101.db"
    db2 = tmp_path / "panelapp_v20230201.db"
    db1.touch()
    db2.touch()

    # Force the same creation time
    ctime = os.path.getctime(str(db1))
    os.utime(str(db2), (ctime, ctime))

    # Act: Call find_most_recent_panel_db
    result = find_most_recent_panel_db(str(tmp_path))

    # Assert: Verify that one of the files is returned
    assert result in [str(db1), str(db2)], "Either file is acceptable if they share ctime."


def test_find_most_recent_panel_date(tmp_path):
    """
    Test `find_most_recent_panel_date` extracts the correct date.

    This test ensures that the function correctly parses and returns the date
    from the name of the most recent valid database file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest fixture providing a temporary directory for the test.

    Asserts
    -------
    - The returned date matches the expected date from the database file name.
    """
    # Arrange: Create a valid database file with a specific date in its name
    db_1 = tmp_path / "panelapp_v20241225.db"
    db_1.touch()

    # Act: Call find_most_recent_panel_date
    expected_date = "2024-12-25"
    found_date = find_most_recent_panel_date(str(tmp_path))

    # Assert: Verify that the correct date is returned
    assert found_date == expected_date