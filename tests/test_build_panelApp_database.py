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
    with patch("os.path.join", return_value="mock_config.json"):
        result = load_config()
    mock_open.assert_called_once_with("mock_config.json", "r")
    assert result == {"server": "mock_server", "headers": {"Authorization": "Bearer mock_token"}}


def test_initialize_api():
    """Test initializing the API."""
    config = {"server": "mock_server", "headers": {"Authorization": "Bearer mock_token"}}
    panels_url, headers = initialize_api(config)
    assert panels_url == "mock_server/api/v1/panels/"
    assert headers == {"Authorization": "Bearer mock_token"}


@patch("requests.get")
def test_fetch_panels(mock_get):
    """Test fetching panels."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": 1, "relevant_disorders": ["R123"]}],
        "next": None,
    }
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response

    result = fetch_panels("mock_url", {"Authorization": "Bearer mock_token"})
    assert result == [{"id": 1, "relevant_disorders": ["R123"]}]
    mock_get.assert_called_once()


@patch("requests.get")
def test_fetch_panel_details(mock_get):
    """Test fetching panel details."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 1, "name": "Mock Panel"}
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_get.return_value = mock_response

    result = fetch_panel_details(1, "mock_url", {"Authorization": "Bearer mock_token"})
    assert result == {"id": 1, "name": "Mock Panel"}
    mock_get.assert_called_once_with("mock_url1/", headers={"Authorization": "Bearer mock_token"})



def test_format_data():
    """Test formatting data into a DataFrame."""
    data = [{"gene_symbol": "GENE1", "relevant_disorders": ["R123"]}]
    df = format_data(data)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 1
    assert df["gene_symbol"].iloc[0] == "GENE1"




if __name__ == "__main__":
    pytest.main()
