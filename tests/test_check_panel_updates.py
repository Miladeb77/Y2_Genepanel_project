import os
import sqlite3
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from PanelGeneMapper.modules.check_panel_updates import (
    get_panel_app_list,
    compare_panel_versions,
)


# Mock data for the PanelApp API response
MOCK_API_RESPONSE = {
    "results": [
        {"id": "panel1", "version": "1.0"},
        {"id": "panel2", "version": "2.0"},
    ],
    "next": None,
}

# Mock data for the local SQLite database
MOCK_LOCAL_DB_DATA = pd.DataFrame({
    "panel_id": ["panel1", "panel2"],
    "version": ["1.0", "1.5"]
})


@pytest.fixture
def mock_api_call():
    """Fixture to mock the PanelApp API calls."""
    with patch("PanelGeneMapper.modules.check_panel_updates.requests.get") as mock_get:
        def side_effect(*args, **kwargs):
            if "page=2" in args[0]:
                return MagicMock(ok=True, json=lambda: {"results": [], "next": None})
            return MagicMock(ok=True, json=lambda: MOCK_API_RESPONSE)
        
        mock_get.side_effect = side_effect
        yield mock_get


@pytest.fixture
def mock_sqlite():
    """Fixture to mock the SQLite database connection."""
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            ("panel1", "1.0"),
            ("panel2", "1.5"),
        ]
        mock_conn.cursor.return_value.fetchall.return_value = [("panel1", "1.0"), ("panel2", "1.5")]
        mock_conn.__enter__.return_value = mock_conn
        yield mock_connect


@pytest.fixture
def mock_filesystem():
    """Fixture to mock the filesystem for databases and logs."""
    with patch("os.listdir") as mock_listdir, patch("os.path.join", side_effect=lambda *args: "/".join(args)):
        mock_listdir.return_value = ["panelapp_v1.db"]
        yield mock_listdir


def test_get_panel_app_list(mock_api_call):
    """Test for get_panel_app_list function."""
    # Call the function
    result = get_panel_app_list()

    # Assert the result matches expected DataFrame
    expected_df = pd.DataFrame({"panel_id": ["panel1", "panel2"], "version": ["1.0", "2.0"]})
    pd.testing.assert_frame_equal(result, expected_df)



