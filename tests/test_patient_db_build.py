import pytest
from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock, call
import pandas as pd
import sqlite3
import os
import logging
import json
import argparse
from datetime import datetime, timedelta

# Import the script functions
from PanelGeneMapper.modules.build_patient_database import (
    setup_logging,
    generate_patient_database,
    save_to_database,
    parse_arguments
)

class TestPatientDatabase(TestCase):
    def test_setup_logging(self):
        """Test logging setup."""
        with patch("logging.FileHandler") as mock_file_handler, \
             patch("logging.StreamHandler") as mock_stream_handler:

            mock_file_handler_instance = MagicMock()
            mock_stream_handler_instance = MagicMock()

            mock_file_handler.return_value = mock_file_handler_instance
            mock_stream_handler.return_value = mock_stream_handler_instance

            setup_logging()

            # Check if handlers are correctly created
            mock_file_handler.assert_called_once()
            mock_stream_handler.assert_called_once()

    @patch("os.listdir", return_value=["panelapp_v20231201.db", "panelapp_v20231101.db"])
    @patch("pandas.DataFrame")
    def test_generate_patient_database(self, mock_df, mock_listdir):
        """Test generating patient database."""
        # Mock the DataFrame constructor
        mock_df.return_value = MagicMock()

        # Generate patient database
        df = generate_patient_database(num_patients=10)

        # Check that the DataFrame was created
        self.assertIsNotNone(df)
        mock_listdir.assert_called_once()

    @patch("pandas.DataFrame.to_sql")
    @patch("sqlite3.connect")
    def test_save_to_database(self, mock_connect, mock_to_sql):
        """Test saving to SQLite database."""
        mock_conn_instance = MagicMock()
        mock_connect.return_value = mock_conn_instance

        # Create a mock DataFrame
        df = pd.DataFrame({"patient_id": ["Patient_1"], "clinical_id": ["R169"], "test_date": ["2024-01-01"]})

        # Call the function
        save_to_database(df, database_name="test_database.db", table_name="test_table")

        # Check that the connection and to_sql were called
        mock_connect.assert_called_once_with("test_database.db")
        mock_to_sql.assert_called_once_with("test_table", mock_conn_instance, if_exists="append", index=False)
        mock_conn_instance.close.assert_called_once()

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_arguments(self, mock_parse_args):
        """Test parsing arguments."""
        mock_parse_args.return_value = argparse.Namespace(
            num_patients=10,
            clinical_ids=["R169", "R419"],
            default_test_date="2024-01-01",
            patient_data=None
        )

        args = parse_arguments()

        # Verify parsed arguments
        self.assertEqual(args.num_patients, 10)
        self.assertEqual(args.clinical_ids, ["R169", "R419"])
        self.assertEqual(args.default_test_date, "2024-01-01")
        self.assertIsNone(args.patient_data)

if __name__ == "__main__":
    pytest.main()