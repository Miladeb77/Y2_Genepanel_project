import pytest
from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock
import os
import gzip
import shutil
import logging

# Import the function to test
from PanelGeneMapper.modules.database_utils import retrieve_latest_panelapp_db

class TestDatabaseUtils(TestCase):

    @patch("os.listdir")
    def test_retrieve_latest_panelapp_db_local_db(self, mock_listdir):
        """Test retrieving the latest PanelApp database from the working directory."""
        mock_listdir.return_value = ["panelapp_v20231201.db", "panelapp_v20231101.db"]

        db_file, is_temp = retrieve_latest_panelapp_db(archive_folder="mock_archive", panelapp_db=None)

        self.assertEqual(db_file, "panelapp_v20231201.db")
        self.assertFalse(is_temp)
        mock_listdir.assert_called_once()

    @patch("os.listdir")
    @patch("gzip.open")
    @patch("shutil.copyfileobj")
    @patch("builtins.open")
    def test_retrieve_latest_panelapp_db_from_archive(self, mock_open, mock_copyfileobj, mock_gzip_open, mock_listdir):
        """Test retrieving and extracting the latest PanelApp database from the archive folder."""
        mock_listdir.side_effect = [[], ["panelapp_v20231101.db.gz", "panelapp_v20231001.db.gz"]]
        mock_gzip_file = MagicMock()
        mock_gzip_open.return_value.__enter__.return_value = mock_gzip_file

        db_file, is_temp = retrieve_latest_panelapp_db(archive_folder="mock_archive", panelapp_db=None)

        self.assertEqual(db_file, "/tmp/panelapp_v20231101.db")
        self.assertTrue(is_temp)
        mock_listdir.assert_called()
        mock_gzip_open.assert_called_once_with(os.path.join("mock_archive", "panelapp_v20231101.db.gz"), 'rb')
        mock_copyfileobj.assert_called_once()

    @patch("os.listdir")
    def test_retrieve_latest_panelapp_db_no_files(self, mock_listdir):
        """Test behavior when no PanelApp database files are found."""
        mock_listdir.return_value = []

        with self.assertRaises(FileNotFoundError):
            retrieve_latest_panelapp_db(archive_folder="mock_archive", panelapp_db=None)

        mock_listdir.assert_called()

    def test_retrieve_latest_panelapp_db_explicit_file(self):
        """Test behavior when an explicit PanelApp database file is provided."""
        db_file, is_temp = retrieve_latest_panelapp_db(archive_folder="mock_archive", panelapp_db="explicit_panelapp.db")

        self.assertEqual(db_file, "explicit_panelapp.db")
        self.assertFalse(is_temp)

if __name__ == "__main__":
    pytest.main()
