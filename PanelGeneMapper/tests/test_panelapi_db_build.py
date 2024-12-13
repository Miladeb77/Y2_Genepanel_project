import pytest
from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock
import os
import logging
import json
from datetime import datetime

# Import the script functions
from PanelGeneMapper.modules import build_panelApp_database 


class TestBuildPanelAppDatabase(TestCase):
    """
    Test cases for the script's main functions.
    """

    def test_set_working_directory(self):
        """Test if the working directory is set correctly."""
        with patch("os.path.dirname", return_value="/mock/script/path"), patch("os.path.abspath", return_value="/mock/script/path"), patch("os.chdir") as mock_chdir:
            script_dir = set_working_directory()
            self.assertEqual(script_dir, "/mock/script/path")
            mock_chdir.assert_called_once_with("/mock/script/path")

    def test_setup_logging(self):
        """Test if logging setup works as expected."""
        with patch("os.path.join", side_effect=lambda *args: "/".join(args)) as mock_join, patch("logging.FileHandler") as mock_file_handler, patch("logging.StreamHandler") as mock_stream_handler:
            script_dir = "/mock/script/path"
            setup_logging(script_dir)

            mock_join.assert_called()
            mock_file_handler.assert_called()
            mock_stream_handler.assert_called()

    def test_load_config(self):
        """Test if the configuration file is loaded correctly."""
        mock_config = {"server": "http://mockserver.com", "headers": {"Authorization": "Bearer mocktoken"}}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config))), patch("os.path.join", return_value="/mock/config/path/config.json"):
            config = load_config("config.json")
            self.assertEqual(config, mock_config)

    def test_initialize_api(self):
        """Test API initialization with valid configuration."""
        mock_config = {"server": "http://mockserver.com", "headers": {"Authorization": "Bearer mocktoken"}}
        panels_url, headers = initialize_api(mock_config)

        self.assertEqual(panels_url, "http://mockserver.com/api/v1/panels/")
        self.assertEqual(headers, {"Authorization": "Bearer mocktoken"})

    @patch("requests.get")
    def test_fetch_panels(self, mock_get):
        """Test fetching panels from the API."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"results": [{"id": "1", "relevant_disorders": ["R1"]}], "next": None}
        mock_get.return_value = mock_response

        panels_url = "http://mockserver.com/api/v1/panels/"
        headers = {"Authorization": "Bearer mocktoken"}

        panels = fetch_panels(panels_url, headers)
        self.assertEqual(len(panels), 1)
        self.assertEqual(panels[0]["id"], "1")

    def test_format_data(self):
        """Test formatting panel data into a DataFrame."""
        mock_data = [
            {
                "panel_id": "1",
                "name": "Test Panel",
                "relevant_disorders": ["R1"],
                "number_of_genes": 10,
                "evidence": ["Test Evidence"]
            }
        ]

        df = format_data(mock_data)
        self.assertEqual(len(df), 1)
        self.assertIn("panel_id", df.columns)
        self.assertIn("relevant_disorders", df.columns)
        self.assertEqual(df.loc[0, "panel_id"], "1")
        self.assertEqual(df.loc[0, "relevant_disorders"], "R1")

if __name__ == "__main__":
    pytest.main()
