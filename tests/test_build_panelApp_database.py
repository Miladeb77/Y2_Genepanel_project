import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import pandas as pd
from datetime import datetime
from PanelGeneMapper.modules.build_panelApp_database import (
    set_working_directory,
    load_config,
    initialize_api,
    fetch_panels,
    fetch_panel_details,
    process_panel_data,
    format_data,
    save_to_database,
)


@patch("builtins.open", new_callable=mock_open, read_data='{"server": "mock_server", "headers": {"Authorization": "Bearer mock_token"}}')
def test_load_config(mock_open):
    """Test loading the configuration file."""
    # Mock `os.path.join` to simulate a file path.
    with patch("os.path.join", return_value="mock_config.json"):
        result = load_config()  # Call the function to load the configuration.
    # Verify that the configuration file was opened correctly.
    mock_open.assert_called_once_with("mock_config.json", "r")
    # Check that the loaded configuration matches the expected mock data.
    assert result == {"server": "mock_server", "headers": {"Authorization": "Bearer mock_token"}}

def test_initialize_api():
    """Test initializing the API."""
    # Mock configuration data.
    config = {"server": "mock_server", "headers": {"Authorization": "Bearer mock_token"}}
    # Call the function to initialize the API.
    panels_url, headers = initialize_api(config)
    # Verify the constructed API endpoint URL.
    assert panels_url == "mock_server/api/v1/panels/"
    # Verify the returned headers.
    assert headers == {"Authorization": "Bearer mock_token"}

@patch("requests.get")
def test_fetch_panels(mock_get):
    """Test fetching panels."""
    # Mock the response from the `requests.get` call.
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": 1, "relevant_disorders": ["R123"]}],  # Mocked panel data.
        "next": None,  # Indicate no further pages.
    }
    mock_response.status_code = 200  # Simulate a successful response.
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response  # Return the mocked response.

    # Call the function to fetch panels.
    result = fetch_panels("mock_url", {"Authorization": "Bearer mock_token"})
    # Verify the returned data matches the mocked panel data.
    assert result == [{"id": 1, "relevant_disorders": ["R123"]}]
    # Ensure the `requests.get` function was called once.
    mock_get.assert_called_once()

@patch("requests.get")
def test_fetch_panel_details(mock_get):
    """Test fetching panel details."""
    # Mock the response from the `requests.get` call.
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 1, "name": "Mock Panel"}  # Mocked panel details.
    mock_response.status_code = 200  # Simulate a successful response.
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response  # Return the mocked response.

    # Call the function to fetch panel details.
    result = fetch_panel_details(1, "mock_url", {"Authorization": "Bearer mock_token"})
    # Verify the returned data matches the mocked panel details.
    assert result == {"id": 1, "name": "Mock Panel"}
    # Ensure the `requests.get` function was called with the correct URL and headers.
    mock_get.assert_called_once_with("mock_url1/", headers={"Authorization": "Bearer mock_token"})

def test_format_data():
    """Test formatting data into a DataFrame."""
    # Mock raw data to format.
    data = [{"gene_symbol": "GENE1", "relevant_disorders": ["R123"]}]
    # Call the function to format the data into a DataFrame.
    df = format_data(data)
    # Verify that the output is a pandas DataFrame.
    assert isinstance(df, pd.DataFrame)
    # Check the number of rows in the DataFrame.
    assert df.shape[0] == 1
    # Verify that the `gene_symbol` column contains the correct value.
    assert df["gene_symbol"].iloc[0] == "GENE1"

if __name__ == "__main__":
    # Run all tests if the script is executed directly.
    pytest.main()

