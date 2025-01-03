import json
import pytest
from unittest.mock import patch
from flask import Flask
from app import app as flask_app

@pytest.fixture(scope="module")
def test_client():
    """
    Creates a Flask test client for sending test requests to routes.

    This fixture sets up a Flask test client with the application's testing 
    configuration enabled, allowing simulated HTTP requests during testing.

    Yields
    ------
    flask.testing.FlaskClient
        A Flask test client instance for sending requests to the app.
    """
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        # Create the test client context and yield it for use in tests
        yield client


@pytest.fixture
def mock_get_hgnc_ids():
    """
    Mocks the `get_hgnc_ids_for_r_code` function to control its output during tests.

    This fixture patches the `get_hgnc_ids_for_r_code` function from the app module, 
    allowing predefined return values or side effects for testing various scenarios.

    Yields
    ------
    unittest.mock.MagicMock
        The mocked version of the `get_hgnc_ids_for_r_code` function.
    """
    with patch('app.get_hgnc_ids_for_r_code') as mocked:
        # Yield the mocked function for use in test cases
        yield mocked


def test_compare_live_panelapp_differences_found(test_client, mock_get_hgnc_ids):
    """
    Test the /compare-live-panelapp endpoint when differences are found between
    existing HGNC IDs and live HGNC IDs.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        Flask test client for simulating HTTP requests.
    mock_get_hgnc_ids : unittest.mock.MagicMock
        Mocked version of the `get_hgnc_ids_for_r_code` function.

    Asserts
    -------
    - HTTP response status code is 200.
    - Response message indicates differences were found.
    - Response contains the expected differences (added and removed HGNC IDs).
    """
    # Arrange: Define test inputs and expected outputs
    clinical_id = "R46"
    existing_hgnc_ids = ["HGNC:12345", "HGNC:67890"]
    live_hgnc_ids = ["HGNC:12345", "HGNC:67890", "HGNC:11111"]  # Added HGNC:11111

    # Mock the live HGNC IDs returned by the external function
    mock_get_hgnc_ids.return_value = live_hgnc_ids

    payload = {
        "clinical_id": clinical_id,
        "existing_hgnc_ids": existing_hgnc_ids
    }

    # Act: Send a POST request to the endpoint
    response = test_client.post(
        '/compare-live-panelapp',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Assert: Validate the response status and data
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["message"] == "Differences found."
    assert "differences" in response_data
    assert "added" in response_data["differences"]
    assert "removed" in response_data["differences"]
    assert response_data["differences"]["added"] == ["HGNC:11111"]
    assert response_data["differences"]["removed"] == []


def test_compare_live_panelapp_no_differences(test_client, mock_get_hgnc_ids):
    """
    Test the /compare-live-panelapp endpoint when no differences are found between
    existing HGNC IDs and live HGNC IDs.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        Flask test client for simulating HTTP requests.
    mock_get_hgnc_ids : unittest.mock.MagicMock
        Mocked version of the `get_hgnc_ids_for_r_code` function.

    Asserts
    -------
    - HTTP response status code is 200.
    - Response message indicates no differences were found.
    - Response does not contain a "differences" key.
    """
    # Arrange: Define test inputs where live and existing HGNC IDs match
    clinical_id = "R46"
    existing_hgnc_ids = ["HGNC:12345", "HGNC:67890"]
    live_hgnc_ids = ["HGNC:12345", "HGNC:67890"]

    # Mock the live HGNC IDs returned by the external function
    mock_get_hgnc_ids.return_value = live_hgnc_ids

    payload = {
        "clinical_id": clinical_id,
        "existing_hgnc_ids": existing_hgnc_ids
    }

    # Act: Send a POST request to the endpoint
    response = test_client.post(
        '/compare-live-panelapp',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Assert: Validate the response status and data
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["message"] == "No changes found. The live PanelApp data matches your current data."
    assert "differences" not in response_data


def test_compare_live_panelapp_missing_clinical_id(test_client):
    """
    Test the /compare-live-panelapp endpoint when the 'clinical_id' is missing in the request.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        Flask test client for simulating HTTP requests.

    Asserts
    -------
    - HTTP response status code is 400.
    - Response contains an appropriate error message.
    """
    # Arrange: Create a payload missing the required 'clinical_id'
    payload = {
        "existing_hgnc_ids": ["HGNC:12345", "HGNC:67890"]
    }

    # Act: Send a POST request to the endpoint
    response = test_client.post(
        '/compare-live-panelapp',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Assert: Validate the error response
    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert response_data["error"] == "Missing clinical_id"


def test_compare_live_panelapp_invalid_existing_hgnc_ids(test_client):
    """
    Test the /compare-live-panelapp endpoint when 'existing_hgnc_ids' is not a list.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        Flask test client for simulating HTTP requests.

    Asserts
    -------
    - HTTP response status code is 400.
    - Response contains an appropriate error message.
    """
    # Arrange: Create a payload with an invalid 'existing_hgnc_ids' value
    payload = {
        "clinical_id": "R46",
        "existing_hgnc_ids": "HGNC:12345"  # Should be a list
    }

    # Act: Send a POST request to the endpoint
    response = test_client.post(
        '/compare-live-panelapp',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Assert: Validate the error response
    assert response.status_code == 400
    response_data = response.get_json()
    assert "error" in response_data
    assert response_data["error"] == "existing_hgnc_ids must be a list"


def test_compare_live_panelapp_internal_server_error(test_client, mock_get_hgnc_ids):
    """
    Test the /compare-live-panelapp endpoint when an internal server error occurs
    while fetching live HGNC IDs.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        Flask test client for simulating HTTP requests.
    mock_get_hgnc_ids : unittest.mock.MagicMock
        Mocked version of the `get_hgnc_ids_for_r_code` function.

    Asserts
    -------
    - HTTP response status code is 500.
    - Response contains an appropriate error message.
    """
    # Arrange: Simulate an API failure during live HGNC ID retrieval
    clinical_id = "R46"
    existing_hgnc_ids = ["HGNC:12345", "HGNC:67890"]

    mock_get_hgnc_ids.side_effect = Exception("API failure")

    payload = {
        "clinical_id": clinical_id,
        "existing_hgnc_ids": existing_hgnc_ids
    }

    # Act: Send a POST request to the endpoint
    response = test_client.post(
        '/compare-live-panelapp',
        data=json.dumps(payload),
        content_type='application/json'
    )

    # Assert: Validate the error response
    assert response.status_code == 500
    response_data = response.get_json()
    assert "error" in response_data
    assert "Failed to retrieve live data for R46" in response_data["error"]