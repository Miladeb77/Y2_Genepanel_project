import os
import json
import tempfile
import pytest
from unittest import mock
import sqlite3
import requests_mock
import re
import importlib
import gzip
import shutil

# ----------------------- Fixtures -----------------------

@pytest.fixture
def test_client():
    """
    Creates a Flask test client using a temporary configuration and database.

    This fixture sets up a fully functional Flask application for testing. 
    It creates temporary configuration files, R Code files, and SQLite 
    databases required for the application to simulate a production-like 
    environment. 

    The `app.load_config` function is mocked to return the temporary 
    configuration files, ensuring isolation from real configurations.

    Yields
    ------
    flask.testing.FlaskClient
        A test client instance configured for the Flask application.
    """
    # Create a temporary directory for all test files
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Paths for test configuration files
        test_app_config = os.path.join(tmpdirname, "app_config.json")
        test_build_panel_config = os.path.join(tmpdirname, "build_panelApp_database_config.json")
        test_r_code_file = os.path.join(tmpdirname, "unique_relevant_disorders.txt")
        test_patient_db = os.path.join(tmpdirname, "patient_database.db")
        test_panel_db = os.path.join(tmpdirname, "panelapp_v20240101.db")

        # Create a test R Code file with mock disorder codes
        with open(test_r_code_file, 'w') as f:
            f.write("R201\nR46\nR58\nR54\nR133\n")  # Write mock clinical disorder codes

        # Create test build_panelApp_database_config.json with PanelApp API details
        build_panel_config = {
            "server": "https://panelapp.genomicsengland.co.uk",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        with open(test_build_panel_config, 'w') as f:
            json.dump(build_panel_config, f)

        # Create test app_config.json with application-specific paths and configs
        app_config = {
            "patient_db_path": test_patient_db,
            "panel_dir": tmpdirname,  # Use tmpdirname for panel directory
            "r_code_file": test_r_code_file,
            "build_panelApp_database_config.json": test_build_panel_config
        }
        with open(test_app_config, 'w') as f:
            json.dump(app_config, f)

        # Create the patient database schema with an example table
        conn = sqlite3.connect(test_patient_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_data (
                patient_id TEXT NOT NULL,
                clinical_id TEXT NOT NULL,
                test_date TEXT NOT NULL,
                panel_retrieved_date TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        # Create the PanelApp database schema with test data
        conn = sqlite3.connect(test_panel_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE panel_info (
                gene_symbol TEXT NOT NULL,
                hgnc_id TEXT NOT NULL,
                relevant_disorders TEXT NOT NULL,
                version_created TEXT NOT NULL
            )
        """)
        # Insert mock data for testing
        cursor.execute("""
            INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
            VALUES ('GeneA', 'HGNC:12345', 'R46', '2024-01-01')
        """)
        cursor.execute("""
            INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
            VALUES ('GeneB', 'HGNC:67890', 'R46', '2024-01-01')
        """)
        cursor.execute("""
            INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
            VALUES ('GeneC', 'HGNC:54321', 'R58', '2024-01-01')
        """)
        conn.commit()
        conn.close()

        # Mock the load_config function to return the temporary configurations
        def mock_load_config_side_effect(path):
            """
            Returns mock configuration data based on the requested file path.

            Parameters
            ----------
            path : str
                Path to the requested configuration file.

            Returns
            -------
            dict
                Configuration data corresponding to the requested path.

            Raises
            ------
            ValueError
                If the path is not recognized.
            """
            if path == "./configuration/app_config.json":
                return app_config
            elif path == test_build_panel_config:
                return build_panel_config
            else:
                raise ValueError(f"Unexpected config path: {path}")

        # Patch the load_config function from the app module
        with mock.patch('app.load_config') as mock_load_config:
            mock_load_config.side_effect = mock_load_config_side_effect

            # Dynamically import the `app` module after mocking the load_config function
            app_module = importlib.import_module('app')
            app = app_module.app

            # Assign test-specific configuration variables to the Flask app
            app.config['PATIENT_DB_PATH'] = app_config["patient_db_path"]
            app.config['PANEL_DIR'] = app_config["panel_dir"]
            app.config['R_CODE_FILE'] = app_config["r_code_file"]

            # Enable testing mode for the Flask app
            app.config['TESTING'] = True

            # Create and yield a test client for sending HTTP requests
            with app.test_client() as client:
                yield client

# ----------------------- Test Cases -----------------------

def test_index(test_client):
    """
    Test the root endpoint '/' to ensure it serves the index.html file.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 200.
    - The response contains the expected HTML structure.
    """
    # Act: Send a GET request to the root endpoint
    response = test_client.get('/')
    
    # Assert: Validate response status and content
    assert response.status_code == 200
    assert b'<html' in response.data  # Check if the response contains HTML content


def test_serve_static_file(test_client):
    """
    Test serving a static file, e.g., style.css.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 200.
    - The response contains the expected CSS content.
    """
    # Arrange: Create a temporary directory and a sample CSS file
    with tempfile.TemporaryDirectory() as tmp_static:
        sample_file_path = os.path.join(tmp_static, 'style.css')
        
        # Write a sample CSS file
        with open(sample_file_path, 'w') as f:
            f.write("body { background-color: #fff; }")
        
        with mock.patch('app.send_from_directory') as mock_send:
            # Mock send_from_directory to return the sample file's content
            with open(sample_file_path, 'rb') as f:
                mock_send.return_value = (f.read(), 200, {'Content-Type': 'text/css'})
            
            # Act: Request the static file
            response = test_client.get('/style.css')
            
            # Assert: Validate the response status and content
            assert response.status_code == 200
            assert b'background-color' in response.data


def test_fetch_patient_data_existing(test_client):
    """
    Test fetching patient data for an existing patient.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 200.
    - The response contains the expected patient data.
    """
    # Arrange: Insert a test patient record into the database
    conn = sqlite3.connect(test_client.application.config['PATIENT_DB_PATH'])
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patient_data (patient_id, clinical_id, test_date, panel_retrieved_date)
        VALUES (?, ?, ?, ?)
    """, ("Patient_12345", "R46", "2024-12-18", "2024-01-01"))
    conn.commit()
    conn.close()

    # Act: Send a GET request to fetch the patient's data
    response = test_client.get('/patient?patient_id=Patient_12345')

    # Assert: Validate the response status and data
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    patient_record = data[0]
    assert patient_record['patient_id'] == "Patient_12345"
    assert patient_record['relevant_disorders'] == "R46"
    assert patient_record['gene_panel'] == ["GeneA", "GeneB"]
    assert patient_record['hgnc_ids'] == ["HGNC:12345", "HGNC:67890"]


def test_fetch_patient_data_non_existing(test_client):
    """
    Test fetching patient data for a non-existing patient.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an appropriate error message.
    """
    # Act: Attempt to fetch data for a non-existent patient
    response = test_client.get('/patient?patient_id=Patient_99999')

    # Assert: Validate the error response
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data
    assert "Please provide an R Code" in data["message"]


def test_missing_patient_id(test_client):
    """
    Test that the endpoint returns a 404 error when `patient_id` is missing.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an error message about the missing patient ID.
    """
    # Act: Send a GET request without the `patient_id` parameter
    response = test_client.get('/patient')

    # Assert: Validate the response
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Patient ID is required."
    assert "You must provide a valid Patient ID to proceed." in data['message']
    assert "Enter a valid Patient ID" in data['prompt']


def test_invalid_patient_id_format(test_client):
    """
    Test that the endpoint returns a 404 error when `patient_id` has an invalid format.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an error message about the invalid format.
    """
    # Act: Send a GET request with an invalid `patient_id` parameter
    response = test_client.get('/patient?patient_id=12345')

    # Assert: Validate the response
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Invalid Patient ID format."
    assert "The Patient ID must start with 'Patient_' followed by one or more digits" in data['message']
    assert "Enter a valid Patient ID in the format 'Patient_<digits>'" in data['prompt']


def test_create_single_patient_record_valid_r_code(test_client):
    """
    Test creating a new patient record with a valid R Code.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 201.
    - The response contains the expected success message and patient record data.
    - The patient record is correctly inserted into the database.
    """
    # Arrange: Define the payload with a valid R Code
    payload = {
        "patient_id": "Patient_54321",
        "r_code": "R46"
    }

    # Act: Send a POST request to create a new patient record
    response = test_client.post('/patient/add', json=payload)

    # Assert: Validate the response status and data
    assert response.status_code == 201
    data = response.get_json()
    assert "message" in data
    assert data["message"] == "New record created successfully."
    new_record = data["new_record"]
    assert new_record["patient_id"] == "Patient_54321"
    assert new_record["relevant_disorders"] == "R46"
    assert new_record["gene_panel"] == ["GeneA", "GeneB"]
    assert new_record["hgnc_ids"] == ["HGNC:12345", "HGNC:67890"]

    # Verify the record is inserted into the database
    conn = sqlite3.connect(test_client.application.config['PATIENT_DB_PATH'])
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM patient_data WHERE patient_id = ?
    """, ("Patient_54321",))
    records = cursor.fetchall()
    conn.close()
    assert len(records) == 1
    assert records[0][0] == "Patient_54321"  # patient_id
    assert records[0][1] == "R46"            # clinical_id


def test_create_single_patient_record_invalid_r_code(test_client):
    """
    Test creating a new patient record with an invalid R Code.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an appropriate error message.
    """
    # Arrange: Define the payload with an invalid R Code
    payload = {
        "patient_id": "Patient_67890",
        "r_code": "R999"  # Invalid R Code
    }

    # Act: Send a POST request to create a new patient record
    response = test_client.post('/patient/add', json=payload)

    # Assert: Validate the error response
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid R Code."


def test_search_older_panelapp_databases_with_r54(test_client):
    """
    Test the /patient/add endpoint when searching for an R Code (`R201`) that is not present
    in the most recent PanelApp database but exists in an older PanelApp database.

    Asserts
    -------
    - The response status code is 201.
    - The response contains the patient record created using data from the older database.
    """

    # Create an older database with relevant data for 'R54'
    older_panel_db_path = os.path.join(test_client.application.config['PANEL_DIR'], "panelapp_v20220101.db.gz")

    # Create the older database with relevant data
    with gzip.open(older_panel_db_path, 'wb') as f_out:
        with tempfile.NamedTemporaryFile(delete=False) as temp_db_file:
            # Initialize the older database schema
            conn = sqlite3.connect(temp_db_file.name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE panel_info (
                    gene_symbol TEXT NOT NULL,
                    hgnc_id TEXT NOT NULL,
                    relevant_disorders TEXT NOT NULL,
                    version_created TEXT NOT NULL
                )
            """)
            # Insert 'R54' with 'GeneX' into the older database
            cursor.execute("""
                INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
                VALUES ('GeneX', 'HGNC:98765', 'R201', '2022-01-01')
            """)
            conn.commit()
            conn.close()

            # Compress the older database to mimic a real `.db.gz` file
            with open(temp_db_file.name, 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)

    # Clean up the temporary uncompressed older database file
    os.remove(temp_db_file.name)

    # Act: Send a POST request with an R Code present only in the older database
    response = test_client.post('/patient/add', json={
        "patient_id": "Patient_67890",
        "r_code": "R201"
    })

    # Assert: Validate that the older database was successfully used
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    data = response.get_json()
    assert data["message"] == "New record created successfully."
    assert data["new_record"]["patient_id"] == "Patient_67890"
    assert data["new_record"]["relevant_disorders"] == "R201"
    assert data["new_record"]["gene_panel"] == ["GeneX"]
    assert data["new_record"]["hgnc_ids"] == ["HGNC:98765"]
    assert data["new_record"]["panel_version"] == "2022-01-01"


def test_fetch_rcode_data_existing(test_client):
    """
    Test fetching data for an existing R Code.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 200.
    - The response contains the expected patient data.
    """
    # Arrange: Insert a test patient record into the database
    conn = sqlite3.connect(test_client.application.config['PATIENT_DB_PATH'])
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patient_data (patient_id, clinical_id, test_date, panel_retrieved_date)
        VALUES (?, ?, ?, ?)
    """, ("Patient_11111", "R46", "2024-12-19", "2024-01-01"))
    conn.commit()
    conn.close()

    # Act: Send a GET request to fetch data for the R Code
    response = test_client.get('/rcode?r_code=R46')

    # Assert: Validate the response status and data
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    patient_record = data[0]
    assert patient_record['patient_id'] == "Patient_11111"
    assert patient_record['relevant_disorders'] == "R46"


def test_fetch_rcode_data_non_existing(test_client):
    """
    Test fetching data for a non-existing R Code.

    Parameters
    ----------
    test_client : flask.testing.FlaskClient
        The test client used to simulate HTTP requests.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an appropriate error message.
    """
    # Act: Attempt to fetch data for a non-existent R Code
    response = test_client.get('/rcode?r_code=R999')  # Invalid R Code

    # Assert: Validate the error response
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data
    assert "not a valid R code" in data["message"]


def test_fetch_multiple_records_with_r46(test_client):
    """
    Test the /rcode endpoint to ensure it retrieves multiple patient records associated with R Code 'R46' 
    present in the most recent panelapp database.

    Asserts
    -------
    - The HTTP response status code is 200.
    - The response contains all patient records associated with 'R46'.
    """
    # Arrange: Insert multiple patient records with 'R46' into the patient database
    conn = sqlite3.connect(test_client.application.config['PATIENT_DB_PATH'])
    cursor = conn.cursor()
    # Insert first patient record
    cursor.execute("""
        INSERT INTO patient_data (patient_id, clinical_id, test_date, panel_retrieved_date)
        VALUES (?, ?, ?, ?)
    """, ("Patient_11111", "R46", "2024-12-25", "2024-01-01"))
    # Insert second patient record
    cursor.execute("""
        INSERT INTO patient_data (patient_id, clinical_id, test_date, panel_retrieved_date)
        VALUES (?, ?, ?, ?)
    """, ("Patient_22222", "R46", "2024-12-26", "2024-01-01"))
    conn.commit()
    conn.close()

    # Act: Send a GET request to fetch records for 'R46'
    response = test_client.get('/rcode?r_code=R46')

    # Assert: Validate the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.get_json()
    assert isinstance(data, list), "Response data should be a list of records."
    assert len(data) == 2, f"Expected 2 records, got {len(data)}."

    # Verify each patient record
    expected_patient_ids = {"Patient_11111", "Patient_22222"}
    actual_patient_ids = {record['patient_id'] for record in data}
    assert actual_patient_ids == expected_patient_ids, "Patient IDs do not match expected values."

    # Optionally, verify other fields if necessary
    for record in data:
        assert record['relevant_disorders'] == "R46", "Relevant disorder does not match 'R46'."
        assert 'gene_panel' in record, "gene_panel field is missing in the record."
        assert 'hgnc_ids' in record, "hgnc_ids field is missing in the record."


def test_add_new_patient_records_with_r133_not_in_any_panelapp(test_client):
    """
    Test the /rcode/handle endpoint to ensure it handles the creation of new patient records
    for a valid R Code 'R133' that does not exist in any PanelApp database.

    Asserts
    -------
    - The HTTP response status code is 404.
    - The response contains an appropriate error message indicating the gene panel is unavailable.
    """

    # Arrange: Create one older PanelApp database without 'R133'
    older_panel_db_path = os.path.join(test_client.application.config['PANEL_DIR'], "panelapp_v20210101.db.gz")

    with gzip.open(older_panel_db_path, 'wb') as f_out:
        with tempfile.NamedTemporaryFile(delete=False) as temp_db_file:
            # Initialize the older PanelApp database schema
            conn = sqlite3.connect(temp_db_file.name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE panel_info (
                    gene_symbol TEXT NOT NULL,
                    hgnc_id TEXT NOT NULL,
                    relevant_disorders TEXT NOT NULL,
                    version_created TEXT NOT NULL
                )
            """)
            # Insert entries without 'R133' into the older database
            cursor.execute("""
                INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
                VALUES ('GeneD', 'HGNC:11223', 'R201', '2020-01-01')
            """)
            cursor.execute("""
                INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
                VALUES ('GeneE', 'HGNC:44556', 'R46', '2020-01-01')
            """)
            cursor.execute("""
                INSERT INTO panel_info (gene_symbol, hgnc_id, relevant_disorders, version_created)
                VALUES ('GeneF', 'HGNC:77889', 'R58', '2020-01-01')
            """)
            conn.commit()
            conn.close()

            # Compress the older database to mimic a real `.db.gz` file
            with open(temp_db_file.name, 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)

    # Clean up the temporary uncompressed older database file
    os.remove(temp_db_file.name)

    # Act: Send a POST request to handle adding new patient records with R Code 'R133'
    response = test_client.post('/rcode/handle', json={
        "response": "Yes",
        "r_code": "R133",
        "patient_ids": ["Patient_44444", "Patient_55555"]
    })

    # Assert: Validate the response
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
    data = response.get_json()
    assert "error" in data, "Response should contain an 'error' field."
    expected_error_message = "The gene panel for the provided R code 'R133' is not available."
    assert expected_error_message in data["error"], \
        f"Error message does not match expected content. Received: {data['error']}"

