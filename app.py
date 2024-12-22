from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import logging
from datetime import datetime
import gzip
import shutil
from multiprocessing import Pool
from filelock import FileLock
import re
import json
import requests

# Initialize the Flask app and specify the static folder for serving files
app = Flask(__name__, static_folder='static')

def setup_logging():
    """
    Sets up logging for the application.

    This function creates a logging directory, configures separate log files for 
    informational and error messages, and sets up console output for real-time 
    monitoring. The logs are saved in a structured format for easy debugging.

    Logs are configured as follows:
    - INFO and higher-level messages are logged to `info_log.log`.
    - ERROR and higher-level messages are logged to `error_log.log`.
    - Console displays INFO and higher-level messages.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    # Directory where logs will be stored
    LOG_DIR = "./logs/Flask_app_logs"  

    # Ensure the logging directory exists, creating it if necessary
    os.makedirs(LOG_DIR, exist_ok=True)

    # Define paths for the two log files
    info_log_path = os.path.join(LOG_DIR, "info_log.log")
    error_log_path = os.path.join(LOG_DIR, "error_log.log")

    # --- Create Handlers ---
    # File handler for logging informational messages (INFO and above)
    info_handler = logging.FileHandler(info_log_path, mode="a")
    info_handler.setLevel(logging.INFO)  # Log all messages of level INFO and above

    # File handler for logging error messages (ERROR and above)
    error_handler = logging.FileHandler(error_log_path, mode="a")
    error_handler.setLevel(logging.ERROR)  # Log only ERROR and above

    # Console handler for real-time logging (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log INFO and above messages to the console

    # --- Define a Common Log Format ---
    # Format: Timestamp, Log Level, and the Message
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Apply the formatter to all handlers
    info_handler.setFormatter(formatter)  # Apply format to INFO log handler
    error_handler.setFormatter(formatter)  # Apply format to ERROR log handler
    console_handler.setFormatter(formatter)  # Apply format to console handler

    # --- Configure the Root Logger ---
    # The root logger aggregates all log messages and directs them to the configured handlers
    logging.basicConfig(
        level=logging.DEBUG,  # Base level captures all messages DEBUG and above
        handlers=[info_handler, error_handler, console_handler]  # Attach handlers to root logger
    )

    # Log a confirmation that the logging setup is complete
    logging.info("Logging has been set up successfully.")

def load_config(config_file_path):
    """
    Load and parse a configuration file in JSON format.

    This function reads a JSON configuration file from the specified file path,
    parses its content, and returns the configuration as a Python dictionary.
    If the file is not found or contains invalid JSON, appropriate errors are logged
    and re-raised to ensure the caller is aware of the issue.

    Parameters
    ----------
    config_file_path : str
        The absolute or relative path to the JSON configuration file.

    Returns
    -------
    dict
        A dictionary containing the configuration data from the JSON file.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    json.JSONDecodeError
        If the file exists but contains invalid JSON.
    """
    try:
        # Attempt to open the JSON configuration file in read mode
        with open(config_file_path, 'r') as config_file:
            # Load the contents of the file into a dictionary
            config = json.load(config_file)
            # Log success message for debugging purposes
            logging.info("Configuration file loaded successfully.")
            return config
    except FileNotFoundError:
        # Log an error message if the file is not found
        logging.error(f"Configuration file not found: {config_file_path}")
        # Re-raise the exception to propagate it to the caller
        raise
    except json.JSONDecodeError:
        # Log an error message if the JSON file contains invalid syntax
        logging.error(f"Error parsing configuration file: {config_file_path}")
        # Re-raise the exception to propagate it to the caller
        raise


######################### Helper Functions ###############################

def decompress_if_needed(file_path):
    """
    Decompress a .gz file if necessary and return the path to the decompressed version.

    This function checks if the given file is a Gzip-compressed file. If it is, the function
    decompresses it to the same directory, ensuring the decompressed file is valid and not
    empty. It uses file locking to prevent race conditions when handling files in parallel
    processes. If the file is already decompressed or not compressed, it returns the
    original path.

    Parameters
    ----------
    file_path : str
        Path to the file, either compressed (ending with `.gz`) or uncompressed.

    Returns
    -------
    str
        The path to the decompressed file if the file was compressed, or the original file path
        if no decompression was needed.

    Raises
    ------
    ValueError
        If the decompressed file is empty after decompression.
    Exception
        If any error occurs during decompression.
    """
    try:
        # Check if the file has a `.gz` extension, indicating it is compressed
        if file_path.endswith('.gz'):
            # Generate the output path by removing the `.gz` extension
            decompressed_file = file_path[:-3]
            # Define a lock file to ensure thread/process-safe operations
            lock_file = f"{decompressed_file}.lock"

            logging.info(f"Preparing to decompress file: {file_path}")

            # Use file locking to prevent race conditions in concurrent environments
            with FileLock(lock_file):
                # Check if decompressed file already exists and is valid (not empty)
                if not os.path.exists(decompressed_file) or os.path.getsize(decompressed_file) == 0:
                    logging.info(f"Decompressing file: {file_path} -> {decompressed_file}")
                    # Open the compressed file for reading and the output file for writing
                    with gzip.open(file_path, 'rb') as f_in, open(decompressed_file, 'wb') as f_out:
                        # Copy the content from the compressed file to the output file
                        shutil.copyfileobj(f_in, f_out)

                    # Verify that the decompressed file is not empty
                    if os.path.getsize(decompressed_file) == 0:
                        raise ValueError(f"Decompressed file is empty: {decompressed_file}")
                else:
                    logging.info(f"Decompressed file already exists and is valid: {decompressed_file}")

            # Return the path to the decompressed file
            return decompressed_file

        # If the file is not compressed, return the original path
        return file_path

    except Exception as e:
        # Log any error encountered during decompression
        logging.error(f"Error while decompressing {file_path}: {e}")
        # Re-raise the exception to propagate it for upstream handling
        raise

def find_relevant_panel_db(panel_retrieved_date, root_dir):
    """
    Search for the PanelApp database file corresponding to a specific retrieval date.

    This function navigates through the given directory and its subdirectories to locate 
    a PanelApp database file whose name matches the specified retrieval date. The file 
    naming convention for the databases is assumed to start with "panelapp_vYYYYMMDD".

    Parameters
    ----------
    panel_retrieved_date : str
        The date the panel was retrieved, in 'YYYY-MM-DD' format.
    root_dir : str
        The root directory where the PanelApp database files are stored.

    Returns
    -------
    str
        The full path to the matching PanelApp database file.

    Raises
    ------
    FileNotFoundError
        If no database file matching the specified date is found.
    """
    try:
        # Format the given date into the expected file prefix, e.g., "20241119" from "2024-11-19"
        target_prefix = f"panelapp_v{panel_retrieved_date.replace('-', '')}"
        logging.info(f"Searching for PanelApp database with prefix: {target_prefix}")

        # Use os.walk to traverse the root directory and all subdirectories
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                # Check if the current file name starts with the target prefix
                if file.startswith(target_prefix):
                    logging.info(f"Found relevant database: {file}")
                    # Return the full path to the matching file
                    return os.path.join(dirpath, file)
        
        # If no matching file is found, raise a FileNotFoundError
        raise FileNotFoundError(f"No PanelApp database found for date {panel_retrieved_date}.")
    
    except FileNotFoundError as e:
        # Log the error if no matching file is found
        logging.error(e)
        # Re-raise the exception to indicate the failure to the caller
        raise

def find_most_recent_panel_db(root_dir):
    """
    Find the most recent uncompressed PanelApp database in the specified directory.

    This function searches the specified root directory (and its subdirectories) 
    for uncompressed PanelApp database files (`.db` files) whose names start with 
    "panelapp_v". It excludes files located in directories named "archive_databases". 
    The most recently created database file is returned.

    Parameters
    ----------
    root_dir : str
        The root directory containing the PanelApp database files.

    Returns
    -------
    str
        The full path to the most recent uncompressed PanelApp database file.

    Raises
    ------
    FileNotFoundError
        If no uncompressed database file is found in the directory.
    Exception
        For any unexpected errors during the search process.
    """
    try:
        # Initialize variables to store the most recent database file and its timestamp
        most_recent_db = None
        most_recent_time = None

        # Traverse the root directory and its subdirectories using os.walk
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                # Identify files that match the criteria: start with "panelapp_v", end with ".db",
                # and are not located in directories named "archive_databases"
                if file.startswith("panelapp_v") and file.endswith(".db") and "archive_databases" not in dirpath:
                    # Get the full path to the current file
                    file_path = os.path.join(dirpath, file)
                    
                    # Retrieve the file's creation time
                    creation_time = os.path.getctime(file_path)

                    # Update the most recent file if this one is newer
                    if most_recent_time is None or creation_time > most_recent_time:
                        most_recent_db = file_path
                        most_recent_time = creation_time

        # If no matching database file is found, raise a FileNotFoundError
        if not most_recent_db:
            raise FileNotFoundError("No uncompressed PanelApp database found.")

        # Log the path of the most recent database file
        logging.info(f"Most recent PanelApp database: {most_recent_db}")

        # Return the path to the most recent database file
        return most_recent_db

    except Exception as e:
        # Log any exceptions encountered during the search process
        logging.error(e)
        # Re-raise the exception to propagate it for upstream handling
        raise

def find_most_recent_panel_date(root_dir):
    """
    Extract the date from the most recent PanelApp database file.

    This function identifies the most recent uncompressed PanelApp database file in 
    the specified directory (using the `find_most_recent_panel_db` function). It 
    then extracts the date embedded in the file name, formats it as 'YYYY-MM-DD', 
    and returns the formatted date.

    Parameters
    ----------
    root_dir : str
        The root directory containing the PanelApp database files.

    Returns
    -------
    str
        The extracted and formatted date from the most recent database file in 'YYYY-MM-DD' format.

    Raises
    ------
    Exception
        If the database file cannot be found, or if the date cannot be extracted or formatted.

    Notes
    -----
    The PanelApp database files are assumed to follow a naming convention like 
    "panelapp_vYYYYMMDD.db". If the file naming convention changes, this function 
    may need to be updated.

    Examples
    --------
    >>> find_most_recent_panel_date("/path/to/databases")
    '2024-11-19'
    """
    try:
        # Use helper function to find the most recent PanelApp database file
        most_recent_db = find_most_recent_panel_db(root_dir)

        # Extract the base name of the file (e.g., "panelapp_v20241119.db")
        base_name = os.path.basename(most_recent_db)

        # Extract the date part from the file name
        # Split by "_v" to isolate the date and remove the ".db" extension
        date_str = base_name.split("_v")[1].split("_")[0].replace(".db", "")

        # Format the extracted date string into 'YYYY-MM-DD' format
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

        # Log the extracted date for debugging or auditing purposes
        logging.info(f"Most recent PanelApp database date: {formatted_date}")

        # Return the formatted date
        return formatted_date

    except Exception as e:
        # Log any exception encountered during processing
        logging.error(f"Error extracting the date from the most recent database: {e}")
        # Re-raise the exception to propagate it for upstream handling
        raise

def extract_genes_and_metadata_from_panel(db_path, clinical_id):
    """
    Extract gene symbols, HGNC IDs, and metadata associated with a specific clinical ID.

    This function connects to a PanelApp SQLite database, queries the `panel_info` table to 
    retrieve the gene symbols and HGNC IDs associated with a given clinical ID, and extracts 
    the `version_created` metadata for the clinical ID. It handles decompression of `.gz` 
    databases if required and ensures cleanup of temporary decompressed files.

    Parameters
    ----------
    db_path : str
        Path to the PanelApp SQLite database, compressed or uncompressed.
    clinical_id : str
        The clinical ID for which data is being retrieved.

    Returns
    -------
    tuple
        A tuple containing:
        - list of str : List of gene symbols associated with the clinical ID.
        - list of str : List of HGNC IDs associated with the clinical ID.
        - str or None : The version created metadata as a string, or None if not available.

    Raises
    ------
    Exception
        If there is an issue reading the database or querying the data.

    Notes
    -----
    The database is expected to have a `panel_info` table with columns:
    - `gene_symbol`: Gene symbols associated with the clinical ID.
    - `hgnc_id`: HGNC IDs associated with the clinical ID.
    - `relevant_disorders`: Clinical IDs stored as substrings in this column.
    - `version_created`: Metadata indicating the database version creation date.

    Examples
    --------
    >>> extract_genes_and_metadata_from_panel('/path/to/database.db.gz', 'R123')
    (['GeneA', 'GeneB'], ['HGNC:12345', 'HGNC:67890'], '2024-11-19')
    """
    decompressed = False  # Flag to track if the database was decompressed
    original_path = db_path  # Save the original database path

    # Decompress the database if it's compressed and get the path to the decompressed file
    db_path = decompress_if_needed(db_path)
    if db_path != original_path:
        decompressed = True  # Mark that the database was decompressed

    try:
        # Log the start of the data extraction process
        logging.info(f"Extracting data for clinical ID: {clinical_id} from {db_path}")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query the `panel_info` table for gene symbols and HGNC IDs associated with the clinical ID
        cursor.execute(
            """
            SELECT DISTINCT gene_symbol, hgnc_id 
            FROM panel_info 
            WHERE relevant_disorders LIKE ?
            """,
            (f"%{clinical_id}%",)  # Match the clinical ID as a substring
        )
        results = cursor.fetchall()

        # Extract gene symbols and HGNC IDs from the query results
        genes = [row[0] for row in results]  # List of gene symbols
        hgnc_ids = [row[1] for row in results]  # List of HGNC IDs

        # Query the `version_created` field for the clinical ID
        cursor.execute(
            """
            SELECT DISTINCT version_created 
            FROM panel_info 
            WHERE relevant_disorders LIKE ?
            """,
            (f"%{clinical_id}%",)
        )
        version_result = cursor.fetchone()
        version_created = version_result[0] if version_result else None  # Get the version metadata

        # Close the database connection
        conn.close()

        # Log the results of the queries
        logging.info(f"Genes found for clinical ID {clinical_id}: {genes}")
        logging.info(f"HGNC IDs found for clinical ID {clinical_id}: {hgnc_ids}")
        logging.info(f"Version created for clinical ID {clinical_id}: {version_created}")

        # Return the extracted data as a tuple
        return genes, hgnc_ids, version_created

    finally:
        # Clean up the decompressed file if it was created
        if decompressed and not os.path.exists(f"{db_path}.lock"):  # Ensure no active locks
            os.remove(db_path)  # Delete the decompressed file
            logging.info(f"Deleted decompressed file: {db_path}")

def get_patient_data(patient_id, db_path):
    """
    Retrieve all records associated with a specific patient ID from the database.

    This function connects to an SQLite database, queries the `patient_data` table,
    and retrieves all records for the specified patient ID. It ensures proper logging 
    for both successful queries and errors.

    Parameters
    ----------
    patient_id : str
        The unique identifier of the patient to search for.
    db_path : str
        The path to the SQLite database file.

    Returns
    -------
    list of tuple
        A list of tuples, where each tuple represents a record from the `patient_data` table.
        Each tuple contains the fields for a single row in the table.

    Raises
    ------
    Exception
        If an error occurs while querying the database.

    Notes
    -----
    The database is expected to have a table named `patient_data` with at least one column
    named `patient_id`. The function uses parameterized queries to prevent SQL injection.

    Examples
    --------
    >>> get_patient_data("Patient_123", "/path/to/database.db")
    [(1, 'Patient_123', 'Condition_A', '2024-12-18'), (2, 'Patient_123', 'Condition_B', '2024-12-19')]
    """
    try:
        # Log the start of the query process
        logging.info(f"Fetching data for patient ID: {patient_id}")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        # Create a cursor to execute SQL commands
        cursor = conn.cursor()

        # Execute a parameterized query to fetch all records for the given patient ID
        cursor.execute(
            """
            SELECT * FROM patient_data
            WHERE patient_id = ?
            """,
            (patient_id,)  # Use a tuple for parameter substitution
        )

        # Fetch all rows that match the query
        records = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Log the successfully fetched records
        logging.info(f"Records fetched for patient ID {patient_id}: {records}")

        # Return the list of records
        return records

    except Exception as e:
        # Log any errors that occur during the database query process
        logging.error(f"Error fetching data for patient ID {patient_id}: {e}")
        # Re-raise the exception to propagate it to the calling function
        raise

def add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, db_path):
    """
    Add a new patient record to the `patient_data` table in the database.

    This function inserts a new record into the `patient_data` table in the SQLite database.
    It includes information such as the patient ID, associated R code, the date the record 
    was inserted, and the PanelApp database retrieval date.

    Parameters
    ----------
    patient_id : str
        The unique identifier of the patient.
    r_code : str
        The relevant disorder (R code) associated with the patient.
    inserted_date : str
        The timestamp when the record is being inserted, formatted as 'YYYY-MM-DD'.
    panel_retrieved_date : str
        The retrieval date of the PanelApp database, formatted as 'YYYY-MM-DD'.
    db_path : str
        The file path to the SQLite database.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If an error occurs during the insertion of the record into the database.

    Notes
    -----
    The database is expected to have a table named `patient_data` with the following schema:
        - `patient_id` (TEXT): Unique identifier for the patient.
        - `clinical_id` (TEXT): The R code associated with the patient.
        - `test_date` (TEXT): The timestamp of when the record was inserted.
        - `panel_retrieved_date` (TEXT): The retrieval date of the PanelApp database.

    Examples
    --------
    >>> add_patient_record(
    ...     patient_id="Patient_123",
    ...     r_code="R46",
    ...     inserted_date="2024-12-18",
    ...     panel_retrieved_date="2024-12-17",
    ...     db_path="/path/to/database.db"
    ... )
    """
    try:
        # Log the attempt to add a new record with provided details
        logging.info(
            f"Adding new patient record: {patient_id}, "
            f"R code: {r_code}, Panel Retrieved Date: {panel_retrieved_date}"
        )

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Create a cursor to execute SQL commands
        cursor = conn.cursor()

        # SQL query to insert the new record into the `patient_data` table
        cursor.execute(
            """
            INSERT INTO patient_data (patient_id, clinical_id, test_date, panel_retrieved_date)
            VALUES (?, ?, ?, ?)
            """,
            (patient_id, r_code, inserted_date, panel_retrieved_date)  # Parameterized query to prevent SQL injection
        )

        # Commit the changes to save the record in the database
        conn.commit()

        # Close the database connection to release resources
        conn.close()

        # Log successful insertion of the patient record
        logging.info(f"Successfully added patient record: {patient_id}")

    except Exception as e:
        # Log the error with details about the patient ID
        logging.error(f"Error adding patient record {patient_id}: {e}")

        # Re-raise the exception to notify the caller of the failure
        raise

def process_patient_record(record, panel_dir):
    """
    Process a single patient record to retrieve its gene panel from the corresponding PanelApp database.

    This function processes a record from the `patients` table by locating the appropriate 
    PanelApp database based on the `panel_retrieved_date`, extracting the gene panel 
    corresponding to the patient's relevant disorder (R code), and returning the combined 
    data in a structured dictionary.

    Parameters
    ----------
    record : tuple
        A single record from the `patients` table containing:
        - patient_id (str): The unique identifier of the patient.
        - relevant_disorders (str): The R code associated with the patient.
        - inserted_date (str): The timestamp when the record was inserted.
        - panel_retrieved_date (str): The date used to locate the appropriate PanelApp database.
    panel_dir : str
        The path to the directory containing the PanelApp database files.

    Returns
    -------
    dict
        A dictionary containing:
        - patient_id (str): The unique identifier of the patient.
        - relevant_disorders (str): The R code associated with the patient.
        - panel_version (str): The version of the PanelApp database.
        - test_date (str): The timestamp when the record was inserted.
        - panel_retrieved_date (str): The date of the associated PanelApp database.
        - gene_panel (list of str): A list of gene symbols related to the R code.
        - hgnc_ids (list of str): A list of HGNC IDs associated with the gene panel.

    Raises
    ------
    Exception
        If an error occurs during processing, such as missing databases or invalid R codes.

    Notes
    -----
    This function uses the following helper functions:
    - `find_relevant_panel_db`: To locate the PanelApp database based on the retrieval date.
    - `extract_genes_and_metadata_from_panel`: To extract gene symbols, HGNC IDs, and version metadata.

    Examples
    --------
    >>> record = ("Patient_123", "R46", "2024-12-18", "2024-12-17")
    >>> panel_dir = "/path/to/databases"
    >>> process_patient_record(record, panel_dir)
    {
        'patient_id': 'Patient_123',
        'relevant_disorders': 'R46',
        'panel_version': '2024-11-19',
        'test_date': '2024-12-18',
        'panel_retrieved_date': '2024-12-17',
        'gene_panel': ['GeneA', 'GeneB'],
        'hgnc_ids': ['HGNC:12345', 'HGNC:67890']
    }
    """
    try:
        # Step 1: Extract relevant fields from the input record tuple
        patient_id, clinical_id, test_date, panel_retrieved_date = record
        logging.info(f"Processing patient ID: {patient_id}, Clinical ID: {clinical_id}")

        # Step 2: Locate the appropriate PanelApp database for the given retrieval date
        logging.info(f"Locating PanelApp database for Panel Retrieved Date: {panel_retrieved_date}")
        panel_db_path = find_relevant_panel_db(panel_retrieved_date, panel_dir)

        # Step 3: Fetch the gene panel and metadata for the relevant disorder (R code)
        logging.info(f"Fetching gene panel for R code {clinical_id} from database: {panel_db_path}")
        genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel(panel_db_path, clinical_id)

        # Step 4: Construct and return a structured dictionary with patient and gene panel data
        return {
            "patient_id": patient_id,  # Unique identifier of the patient
            "relevant_disorders": clinical_id,  # The R code associated with the patient
            "panel_version": version_created,  # Version of the PanelApp database
            "test_date": test_date,  # Timestamp when the record was inserted
            "panel_retrieved_date": panel_retrieved_date,  # Date used to locate the database
            "gene_panel": genes,  # List of gene symbols related to the R code
            "hgnc_ids": hgnc_ids,  # List of HGNC IDs associated with the genes
        }

    except Exception as e:
        # Log the error along with the specific record details for debugging
        logging.error(f"Error processing patient record {record}: {e}")

        # Re-raise the exception to allow higher-level error handling
        raise

def get_r_code_data(r_code, db_path):
    """
    Fetch all patient records from the `patient_data` table associated with a given R code.

    This function connects to the specified SQLite database, queries the `patient_data` table, 
    and retrieves all records where the `clinical_id` matches the provided R code. It ensures 
    secure database access using parameterized queries to prevent SQL injection.

    Parameters
    ----------
    r_code : str
        The R code to search for in the `clinical_id` field of the `patient_data` table.
    db_path : str
        The file path to the SQLite database containing the `patient_data` table.

    Returns
    -------
    list of tuple
        A list of tuples, where each tuple represents a record from the `patient_data` table 
        matching the given R code. Each tuple contains the fields for a single row in the table.

    Raises
    ------
    Exception
        If there is an issue connecting to the database or executing the query.

    Notes
    -----
    The database is expected to have a `patient_data` table with the following columns:
    - `patient_id` (TEXT): Unique identifier for the patient.
    - `clinical_id` (TEXT): The R code associated with the patient.
    - `test_date` (TEXT): The timestamp of when the record was inserted.
    - `panel_retrieved_date` (TEXT): The retrieval date of the PanelApp database.

    Examples
    --------
    >>> get_r_code_data("R46", "/path/to/database.db")
    [('Patient_123', 'R46', '2024-12-18', '2024-12-17'),
     ('Patient_456', 'R46', '2024-12-19', '2024-12-17')]
    """
    try:
        # Log the start of the fetch operation
        logging.info(f"Fetching records for R code: {r_code} from database: {db_path}")

        # Step 1: Establish a connection to the SQLite database
        conn = sqlite3.connect(db_path)

        # Step 2: Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Step 3: Define a parameterized SQL query to search for records with the given R code
        query = """
        SELECT * 
        FROM patient_data 
        WHERE clinical_id = ?
        """
        
        # Execute the query with the R code as a parameter to prevent SQL injection
        cursor.execute(query, (r_code,))

        # Step 4: Fetch all rows that match the query
        records = cursor.fetchall()

        # Step 5: Close the database connection to release resources
        conn.close()

        # Log the successful retrieval of records
        logging.info(f"Records fetched for R code {r_code}: {records}")

        # Step 6: Return the list of fetched records
        return records

    except Exception as e:
        # Log any exceptions encountered during the process
        logging.error(f"Error fetching records for R code {r_code}: {e}")

        # Re-raise the exception to notify the caller of the failure
        raise

def get_hgnc_ids_for_r_code(r_code):
    """
    Fetch HGNC IDs for a given R code from the PanelApp API.

    This function loads the application configuration from `app_config.json`, retrieves the
    path to `build_panelApp_database_config.json`, and loads its content to extract API server
    and headers configuration. It queries the PanelApp API to find panels matching the given
    R code, fetches detailed gene information for each matching panel, and extracts the HGNC IDs.

    Parameters
    ----------
    r_code : str
        The R code to search for.

    Returns
    -------
    list of str
        A list of HGNC IDs associated with the given R code.

    Raises
    ------
    Exception
        If there is an error during API requests or file handling.

    Notes
    -----
    The function uses the following files:
    - `app_config.json`: Contains the path to `build_panelApp_database_config.json`.
    - `build_panelApp_database_config.json`: Contains API configuration details.

    The PanelApp API is expected to return JSON responses with the following structures:
    - A list of panels, each containing `relevant_disorders`.
    - Panel details containing a `genes` list, where each gene has `gene_data.hgnc_id`.

    Examples
    --------
    >>> get_hgnc_ids_for_r_code("R46")
    ['HGNC:12345', 'HGNC:67890']
    """
    try:
        # Step 1: Load main application configuration
        app_config = load_config("./config/app_config.json")
        # Retrieve the path to `build_panelApp_database_config.json` from the main config
        build_panel_config_path = app_config["build_panelApp_database_config.json"]

        # Step 2: Load API configuration from `build_panelApp_database_config.json`
        build_panel_config = load_config(build_panel_config_path)
        # Extract API server URL and request headers
        server = build_panel_config["server"]
        headers = build_panel_config["headers"]

        # Step 3: Initialize variables for API interaction
        panels_url = f"{server}/api/v1/panels/"  # Base URL for fetching panels
        all_panels = []  # List to store all panels fetched from the API
        page = 1  # Start with the first page of API results

        # Step 4: Fetch all panels from the API in a paginated manner
        while True:
            # Make a GET request to fetch panels for the current page
            response = requests.get(panels_url, headers=headers, params={"page": page})
            # Check if the response is valid and contains JSON data
            if response.status_code == 200 and response.headers.get("Content-Type") == "application/json":
                data = response.json()  # Parse the response JSON
                panels = data.get("results", [])  # Extract panel results from the JSON
                all_panels.extend(panels)  # Append the current page of panels to the list
                if data.get("next") is None:  # Stop if there are no more pages
                    break
                page += 1  # Increment the page counter for the next API request
            else:
                # Log an error if the API response is invalid or fails
                logging.error(f"Failed to fetch panels from {panels_url}: {response.status_code}")
                break

        # Step 5: Filter panels that contain the R code in their `relevant_disorders` field
        matching_panels = [p for p in all_panels if r_code in p.get("relevant_disorders", [])]

        # Step 6: Fetch detailed information for each matching panel and extract HGNC IDs
        hgnc_ids = []  # List to store HGNC IDs extracted from the panels
        for panel in matching_panels:
            panel_id = panel["id"]  # Extract the panel ID
            panel_detail_url = f"{server}/api/v1/panels/{panel_id}/"  # URL for panel details
            # Make a GET request to fetch detailed information for the panel
            response = requests.get(panel_detail_url, headers=headers)
            if response.status_code == 200 and response.headers.get("Content-Type") == "application/json":
                panel_details = response.json()  # Parse the panel details JSON
                # Iterate through genes in the panel and extract HGNC IDs
                for gene in panel_details.get("genes", []):
                    gene_data = gene.get("gene_data", {})  # Extract `gene_data` dictionary
                    hgnc_id = gene_data.get("hgnc_id")  # Get the HGNC ID
                    if hgnc_id:
                        hgnc_ids.append(hgnc_id)  # Add the HGNC ID to the list

        # Step 7: Return the list of HGNC IDs
        return hgnc_ids

    except Exception as e:
        # Log any exception that occurs during the process
        logging.error(f"Error in get_hgnc_ids_for_r_code: {e}")
        # Re-raise the exception to allow higher-level error handling
        raise


############################ ENDPOINTS #####################################

@app.route('/')
def index():
    """
    Serve the `index.html` file for the root URL of the application.

    This function handles requests to the root URL ("/") and serves the `index.html`
    file from the application's static folder. It acts as the main entry point for
    users accessing the application interface.

    Parameters
    ----------
    None

    Returns
    -------
    Response
        A Flask response object containing the `index.html` file from the static folder.

    Notes
    -----
    - This function assumes that the `index.html` file is located in the static folder
      of the Flask application (i.e., `app.static_folder`).
    - The `send_from_directory` function is used to serve the file securely.

    Examples
    --------
    If the `static_folder` is set to "static" and contains an `index.html` file,
    accessing the root URL (http://localhost:5000/) will serve this file.

    >>> # Example in Flask app
    >>> app = Flask(__name__, static_folder="static")
    >>> @app.route('/')
    ... def index():
    ...     return send_from_directory(app.static_folder, 'index.html')
    """
    # Log when the root route is accessed
    logging.info("Serving index.html for the root route.")

    # Serve the `index.html` file from the static folder
    # The `send_from_directory` function ensures the file is served securely
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """
    Serve static files from the application's static folder.

    This function handles requests for specific files in the static folder by
    serving the requested file securely. The `<path:filename>` route parameter
    allows serving files nested within subdirectories of the static folder.

    Parameters
    ----------
    filename : str
        The relative path to the requested file within the static folder. This
        may include subdirectory paths (e.g., `css/style.css` or `images/logo.png`).

    Returns
    -------
    Response
        A Flask response object containing the requested static file.

    Notes
    -----
    - The `send_from_directory` function ensures secure file serving by restricting
      access to files within the specified directory (`app.static_folder`).
    - The static folder is defined by `app.static_folder`, which should be set
      during Flask app initialization (default: `static`).

    Examples
    --------
    If the static folder contains the following structure:
    ```
    static/
    ├── css/
    │   └── style.css
    ├── images/
    │   └── logo.png
    └── script.js
    ```

    Accessing the following URLs will serve these files:
    - `http://localhost:5000/css/style.css` -> Serves `static/css/style.css`
    - `http://localhost:5000/images/logo.png` -> Serves `static/images/logo.png`
    - `http://localhost:5000/script.js` -> Serves `static/script.js`
    """
    # Log the name of the static file being served for traceability
    logging.info(f"Serving static file: {filename}")

    # Serve the requested file securely from the static folder
    # `send_from_directory` restricts access to the specified directory
    return send_from_directory(app.static_folder, filename)

@app.route('/patient', methods=['GET'])
def fetch_patient_data():
    """
    Handle GET requests to fetch patient data or prompt for an R Code if the patient does not exist.

    This endpoint processes requests to retrieve patient information based on the provided
    `patient_id` query parameter. If the patient does not exist in the database, the endpoint
    prompts the user to provide an R Code to create a new record.

    Parameters
    ----------
    None (query parameter: `patient_id` is expected in the request)

    Returns
    -------
    Response
        JSON response containing patient data, or a prompt to provide an R Code if no data is found.
        HTTP status codes:
        - 200: Success, patient data is returned.
        - 404: Patient ID is missing, invalid, or no records are found.
        - 500: Internal server error.

    Notes
    -----
    - The `patient_id` query parameter must follow the format `Patient_<digits>`.
    - Uses `get_patient_data` to query the database and `process_patient_record` to enrich records.

    Examples
    --------
    Valid request:
    >>> GET /patient?patient_id=Patient_12345
    Response: HTTP 200 with patient data.

    Invalid patient ID:
    >>> GET /patient?patient_id=12345
    Response: HTTP 404 with an error message about the format.

    Patient not found:
    >>> GET /patient?patient_id=Patient_67890
    Response: HTTP 404 prompting for an R Code.

    Internal server error:
    >>> GET /patient
    Response: HTTP 500 with an error message.
    """
    try:
        # Step 1: Extract the patient ID from the query parameters
        patient_id = request.args.get('patient_id')

        # Step 2: Validate if the patient ID is provided
        if not patient_id:
            logging.warning("Patient ID is missing in the request.")
            return jsonify({
                "error": "Patient ID is required.",
                "message": "You must provide a valid Patient ID to proceed.",
                "prompt": "Enter a valid Patient ID (e.g., Patient_12345):"
            }), 404

        # Step 3: Validate the format of the patient ID using a regular expression
        if not re.match(r"^Patient_\d+$", patient_id):
            logging.warning(f"Invalid Patient ID format: {patient_id}")
            return jsonify({
                "error": "Invalid Patient ID format.",
                "message": (
                    "The Patient ID must start with 'Patient_' followed by one or more digits "
                    "(e.g., 'Patient_12345')."
                ),
                "prompt": "Enter a valid Patient ID in the format 'Patient_<digits>':"
            }), 404

        # Step 4: Query the database for records matching the patient ID
        logging.info(f"Searching for records for Patient ID: {patient_id}")
        records = get_patient_data(patient_id, patient_db_path)

        # Step 5: If no records are found, prompt the user to provide an R Code
        if not records:
            logging.info(f"No records found for Patient ID: {patient_id}")
            return jsonify({
                "message": f"No records found for Patient ID '{patient_id}'. "
                           f"Please provide an R Code to create a new record.",
                "prompt": "Please provide the R Code for this patient to create a new record."
            }), 404

        # Step 6: Process the records and enrich them with gene panel information
        logging.info(f"Processing records for Patient ID: {patient_id}")
        with Pool() as pool:
            results = pool.starmap(
                process_patient_record,
                [(record, panel_dir) for record in records]
            )

        # Step 7: Log the processed data and return it as a JSON response
        logging.debug(f"Processed data for Patient ID {patient_id}: {results}")
        return jsonify(results), 200

    except Exception as e:
        # Step 8: Log any unexpected errors and return an HTTP 500 response
        logging.error(f"Error in /patient GET route: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/patient/add', methods=['POST'])
def create_single_patient_record():
    """
    Validate the R Code provided by the user and create a new patient record.

    This endpoint handles the creation of a new patient record after validating the
    provided R Code against a list of valid R Codes. If the R Code is valid, it retrieves
    the associated gene panel from the most recent or older PanelApp databases and
    stores the new record in the database.

    Parameters
    ----------
    None (expects a JSON payload in the request body):
        {
            "patient_id": str,  # The unique identifier for the patient
            "r_code": str       # The R Code associated with the patient
        }

    Returns
    -------
    Response
        JSON response with the status of the operation:
        - 201: New record created successfully.
        - 404: Missing or invalid R Code, or gene panel not found.
        - 500: Internal server error.

    Notes
    -----
    - The function validates the R Code against a file of valid R Codes.
    - If the R Code is valid, it retrieves the gene panel from the PanelApp database.
    - If no gene panel is found in the most recent database, it searches older databases.

    Examples
    --------
    Valid request:
    >>> POST /patient/add
    >>> {
            "patient_id": "Patient_12345",
            "r_code": "R46"
        }
    Response: HTTP 201 with the new patient record.

    Invalid R Code:
    >>> POST /patient/add
    >>> {
            "patient_id": "Patient_12345",
            "r_code": "INVALID_R"
        }
    Response: HTTP 404 with an error message about the R Code.
    """
    try:
        # Step 1: Retrieve patient data from the JSON request body
        data = request.json
        patient_id = data.get('patient_id')
        r_code = data.get('r_code')

        # Step 2: Validate that the R Code is provided
        if not r_code:
            logging.warning("R Code is missing in the request.")
            return jsonify({
                "error": "Missing required field.",
                "missing_field": {
                    "field": "r_code",
                    "message": "You must provide a valid R Code to proceed.",
                    "prompt": "Enter a valid R Code (e.g., R123):"
                }
            }), 404

        # Step 3: Load valid R Codes from the file and validate the provided R Code
        with open(r_code_file, "r") as f:
            valid_r_codes = {line.strip() for line in f.readlines()}  # Load valid R Codes into a set

        if r_code not in valid_r_codes:
            logging.warning(f"Invalid R Code: {r_code}")
            return jsonify({
                "error": "Invalid R Code.",
                "message": "This is not a valid R Code. Please provide a valid one.",
                "prompt": "Enter a valid R Code:"
            }), 404

        # Step 4: Initialize variables for processing
        inserted_date = datetime.now().strftime("%Y-%m-%d")  # Record the current date

        try:
            # Step 5: Attempt to retrieve the most recent PanelApp database
            panel_retrieved_date = find_most_recent_panel_date(panel_dir)
            panel_db_path = find_most_recent_panel_db(panel_dir)

            # Step 6: Extract genes and metadata for the R Code from the database
            genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel(panel_db_path, r_code)

            # Step 7: If no gene panel is found, search older PanelApp databases
            if not genes:
                logging.info(f"R Code {r_code} not found in the most recent PanelApp database. Searching older databases.")

                genes = None
                hgnc_ids = None
                version_created = None
                panel_retrieved_date = None  # Reset panel retrieved date

                max_iterations = 1000  # Set a safety limit for iterations
                iteration_count = 0

                for dirpath, _, filenames in os.walk(panel_dir):
                    for file in filenames:
                        if file.endswith(".db.gz"):
                            panel_db_path = os.path.join(dirpath, file)
                            iteration_count += 1

                            if iteration_count > max_iterations:
                                logging.error("Exceeded maximum iterations while searching for databases.")
                                raise RuntimeError("Exceeded maximum iterations while searching for databases.")

                            # Decompress the database file if needed
                            decompressed_db_path = decompress_if_needed(panel_db_path)

                            # Attempt to extract gene data from the database
                            genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel(panel_db_path, r_code)

                            if genes:  # If genes are found, exit the loop
                                panel_retrieved_date = os.path.basename(panel_db_path).split("_v")[1].split("_")[0]
                                panel_retrieved_date = f"{panel_retrieved_date[:4]}-{panel_retrieved_date[4:6]}-{panel_retrieved_date[6:]}"
                                logging.info(f"R Code {r_code} found in older PanelApp database: {file}.")
                                break

                    if genes:
                        break  # Exit the outer loop if a match is found

            # Step 8: If no gene panel is found, return an error response
            if not genes:
                logging.warning(f"Gene panel for R Code {r_code} is not available in any PanelApp database.")
                return jsonify({
                    "error": f"The gene panel for the provided R Code '{r_code}' is not available.",
                    "message": "This might be because the R Code is old, deleted, or altered."
                }), 404

            # Step 9: Add the new patient record to the database
            add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, patient_db_path)

            # Step 10: Return success response with the new record details
            logging.info(f"New record created for Patient ID {patient_id} with R Code {r_code}")
            return jsonify({
                "message": "New record created successfully.",
                "new_record": {
                    "patient_id": patient_id,
                    "relevant_disorders": r_code,
                    "panel_version": version_created,
                    "test_date": inserted_date,
                    "panel_retrieved_date": panel_retrieved_date,
                    "gene_panel": genes,
                    "hgnc_ids": hgnc_ids
                }
            }), 201

        except Exception as e:
            # Log errors during database processing and return an internal server error response
            logging.error(f"Error processing Patient ID {patient_id} for R Code {r_code}: {e}")
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        # Log any unexpected errors and return an internal server error response
        logging.error(f"Error in /patient/add POST route: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/rcode', methods=['GET'])
def fetch_rcode_data():
    """
    Fetch records associated with a specific R Code.

    This endpoint handles requests to search for records associated with a provided
    R Code. It validates the R Code against a list of valid R Codes and checks the
    database for related patient records. If no records are found, it prompts the user
    for further input. If records are found, they are processed and returned.

    Parameters
    ----------
    None (expects query parameter `r_code` in the request)

    Returns
    -------
    Response
        JSON response containing the status of the operation:
        - 200: Successfully retrieved and processed records.
        - 404: Missing or invalid R Code, or no records found.
        - 500: Internal server error.

    Notes
    -----
    - The R Code is validated against a file of valid R Codes (`unique_relevant_disorders.txt`).
    - If no records are found in the database, it prompts the user to provide input.
    - If records are found, they are processed using the `process_patient_record` function.

    Examples
    --------
    Valid request:
    >>> GET /rcode?r_code=R46
    Response: HTTP 200 with records.

    Invalid R Code:
    >>> GET /rcode?r_code=INVALID_R
    Response: HTTP 404 with an error message about the R Code.

    R Code not found:
    >>> GET /rcode?r_code=R123
    Response: HTTP 404 prompting the user for further input.

    Internal server error:
    >>> GET /rcode
    Response: HTTP 500 with an error message.
    """
    try:
        # Step 1: Retrieve the R Code from query parameters
        r_code = request.args.get('r_code')  # Get user-provided R Code
        if not r_code:
            # Log and return a response if the R Code is missing
            logging.warning("R Code is missing in the request.")
            return jsonify({
                "error": "Rcode is required.",
                "message": "You must provide a valid Rcode to proceed.",
                "prompt": "Enter a valid Rcode (e.g., R58):"
            }), 404

        # Step 2: Validate the R Code against the file of valid R Codes
        logging.info(f"Validating R Code: {r_code}")
        with open(r_code_file, "r") as f:
            valid_r_codes = {line.strip() for line in f.readlines()}  # Load valid R Codes into a set

        if r_code not in valid_r_codes:
            # Log and return a response if the R Code is invalid
            logging.warning(f"Invalid R Code: {r_code}")
            return jsonify({
                "message": "This is not a valid R code. Please provide a valid one.",
                "prompt": "Enter a valid R code:"
            }), 404

        # Step 3: Fetch records associated with the R Code from the database
        logging.info(f"Fetching records for R Code: {r_code}")
        records = get_r_code_data(r_code, patient_db_path)

        if not records:
            # Log and return a structured response if no records are found
            logging.info(f"No records found for R Code: {r_code}")
            return jsonify({
                "message": f"R code '{r_code}' not found.",
                "rcode": r_code,
                "prompt": (
                    "No patients have had this R code analysis. "
                    "Do you have any patients that have had an analysis with this R code? "
                    "Reply 'Yes' or 'No'."
                )
            }), 404

        # Step 4: Process records if they are found
        if records:
            logging.info(f"Processing records for R Code: {r_code}")
            # Use multiprocessing for efficient parallel processing
            with Pool() as pool:
                results = pool.starmap(
                    process_patient_record,
                    [(record, panel_dir) for record in records]
                )
            # Return processed records as a JSON response
            logging.info(f"Processed {len(results)} records for R Code: {r_code}")
            return jsonify(results), 200

    except Exception as e:
        # Log and return an internal server error response for unexpected errors
        logging.error(f"Error in /rcode route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/rcode/handle', methods=['POST'])
def handle_rcode():
    """
    Handle user responses for unrecognized R Code searches.

    This endpoint processes the user's response to the prompt about R Codes that are not
    found in the database. Depending on the user's response:
    - If "No", the operation terminates, and no action is taken.
    - If "Yes", the endpoint expects a list of patient IDs to create new records.
    - If neither, the endpoint returns an error with a prompt for clarification.

    Parameters
    ----------
    None (expects a JSON payload in the request body):
        {
            "response": str,        # User response ('Yes' or 'No')
            "r_code": str,          # R Code associated with the operation
            "patient_ids": list     # List of patient IDs (required if response is 'Yes')
        }

    Returns
    -------
    Response
        JSON response with the status of the operation:
        - 200: No action taken (user responded "No").
        - 201: New records created successfully (user responded "Yes").
        - 404: Missing/invalid input or no gene panel found for the R Code.
        - 500: Internal server error.

    Notes
    -----
    - The endpoint validates the R Code and uses the most recent PanelApp database
      to retrieve associated gene panels. If not found, it searches older databases.
    - Each patient ID provided is processed individually.

    Examples
    --------
    User says "Yes" with patient IDs:
    >>> POST /rcode/handle
    >>> {
            "response": "Yes",
            "r_code": "R46",
            "patient_ids": ["Patient_123", "Patient_456"]
        }
    Response: HTTP 201 with new records.

    User says "No":
    >>> POST /rcode/handle
    >>> {
            "response": "No",
            "r_code": "R46"
        }
    Response: HTTP 200 with a message indicating no action was taken.
    """
    try:
        # Step 1: Retrieve the user response and R Code from the JSON payload
        user_response = request.json.get('response')  # User's response ('Yes' or 'No')
        r_code = request.json.get('r_code')  # The R Code provided earlier

        # Step 2: Validate input for presence of R Code and user response
        if not r_code or not user_response:
            logging.warning("Missing R code or user response in the request.")
            return jsonify({"error": "R code and user response are required."}), 400

        # Step 3: Handle the "No" response
        if user_response.lower() == "no":
            logging.info(f"User indicated no patients exist for the R code: {r_code}.")
            return jsonify({"message": "No action taken. Returning to main page."}), 200

        # Step 4: Handle the "Yes" response
        if user_response.lower() == "yes":
            # Step 4.1: Retrieve the list of patient IDs
            patient_ids = request.json.get('patient_ids')  # Expect a list of patient IDs
            if not patient_ids or len(patient_ids) == 0:
                logging.warning("Empty patient IDs provided for new record creation.")
                return jsonify({
                    "error": "Empty patient list provided",
                    "message": "Please provide a non-empty list of patient IDs.",
                    "prompt": "Enter the patient IDs as a list"
                }), 404

            # Step 4.2: Initialize variables for record creation
            inserted_date = datetime.now().strftime("%Y-%m-%d")  # Current date for the record
            new_records = []  # List to hold details of newly created records

            # Step 4.3: Process each patient ID
            for patient_id in patient_ids:
                try:
                    # Use the most recent PanelApp database
                    panel_retrieved_date = find_most_recent_panel_date(panel_dir)
                    panel_db_path = find_most_recent_panel_db(panel_dir)

                    # Attempt to extract the gene panel and metadata for the R Code
                    genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel(panel_db_path, r_code)

                    # If no gene panel is found in the most recent database, search older databases
                    if not genes:
                        logging.info(f"R code {r_code} not found in the most recent PanelApp database. Searching older databases.")

                        genes = None
                        hgnc_ids = None
                        version_created = None
                        panel_retrieved_date = None  # Reset panel retrieved date

                        # Search through older databases
                        max_iterations = 1000  # Safety limit for iterations
                        iteration_count = 0

                        for dirpath, _, filenames in os.walk(panel_dir):
                            for file in filenames:
                                if file.endswith(".db.gz"):
                                    panel_db_path = os.path.join(dirpath, file)
                                    iteration_count += 1

                                    if iteration_count > max_iterations:
                                        logging.error("Exceeded maximum iterations while searching for databases.")
                                        raise RuntimeError("Exceeded maximum iterations while searching for databases.")

                                    # Decompress the database file if needed
                                    decompressed_db_path = decompress_if_needed(panel_db_path)

                                    # Try extracting gene data
                                    genes, hgnc_ids, version_created = extract_genes_and_metadata_from_panel(panel_db_path, r_code)

                                    if genes:  # Exit loop if genes are found
                                        panel_retrieved_date = os.path.basename(panel_db_path).split("_v")[1].split("_")[0]
                                        panel_retrieved_date = f"{panel_retrieved_date[:4]}-{panel_retrieved_date[4:6]}-{panel_retrieved_date[6:]}"
                                        logging.info(f"R code {r_code} found in older PanelApp database: {file}.")
                                        break

                            if genes:
                                break  # Exit outer loop if gene panel is found

                    # If no gene panel is found in any database, return an error response
                    if not genes:
                        logging.warning(f"Gene panel for R code {r_code} is not available in any PanelApp database.")
                        return jsonify({
                            "error": f"The gene panel for the provided R code '{r_code}' is not available.",
                            "message": "This might be because the R code is old, deleted, or altered."
                        }), 404

                    # Add the new patient record to the database
                    add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, patient_db_path)

                    # Append the new record to the response
                    new_records.append({
                        "patient_id": patient_id,
                        "relevant_disorders": r_code,
                        "panel_version": version_created,
                        "test_date": inserted_date,
                        "panel_retrieved_date": panel_retrieved_date,
                        "gene_panel": genes,
                        "hgnc_ids": hgnc_ids
                    })

                except Exception as e:
                    logging.error(f"Error processing patient ID {patient_id} for R code {r_code}: {e}")
                    return jsonify({"error": str(e)}), 500

            # Step 4.4: Return a success response with the newly created records
            logging.info(f"New records created for R code {r_code} and patients: {patient_ids}")
            return jsonify({
                "message": "New records created successfully.",
                "new_records": new_records
            }), 201

        # Step 5: Handle unexpected responses
        logging.warning(f"Unexpected response: {user_response}")
        return jsonify({
            "error": "Invalid response.",
            "message": "Please reply with either 'Yes' or 'No'.",
            "prompt": "Enter 'Yes' if you want to provide patient IDs, or 'No' to cancel the operation."
        }), 404

    except Exception as e:
        # Log any unexpected errors and return a 500 error response
        logging.error(f"Error in /rcode/handle route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/compare-live-panelapp', methods=['POST'])
def compare_live_panelapp():
    """
    Compare the given HGNC IDs with live data from PanelApp.

    This endpoint retrieves live HGNC IDs for a given clinical ID (R Code) from PanelApp
    and compares them with the provided existing HGNC IDs. It reports any differences
    (IDs added or removed) between the two sets.

    Parameters
    ----------
    None (expects a JSON payload in the request body):
        {
            "clinical_id": str,          # The R Code associated with the operation
            "existing_hgnc_ids": list    # List of existing HGNC IDs to compare
        }

    Returns
    -------
    Response
        JSON response with the status of the operation:
        - 200: If the comparison is successful.
          {
              "message": "Differences found.",
              "differences": {
                  "added": ["HGNC:1234", ...],  # HGNC IDs in live data but not in existing data
                  "removed": ["HGNC:5678", ...] # HGNC IDs in existing data but not in live data
              }
          }
        - 200: If no differences are found.
          {
              "message": "No changes found. The live PanelApp data matches your current data."
          }
        - 400: For invalid input or missing data.
        - 500: For internal server errors or issues fetching live data.

    Notes
    -----
    - Uses `get_hgnc_ids_for_r_code` to retrieve live HGNC IDs from PanelApp.
    - Compares the provided list (`existing_hgnc_ids`) with the live list (`live_hgnc_ids`).
    - Reports any differences in a structured JSON response.

    Examples
    --------
    Valid request:
    >>> POST /compare-live-panelapp
    >>> {
            "clinical_id": "R46",
            "existing_hgnc_ids": ["HGNC:12345", "HGNC:67890"]
        }
    Response: HTTP 200 with added and removed IDs.

    No differences found:
    >>> POST /compare-live-panelapp
    >>> {
            "clinical_id": "R46",
            "existing_hgnc_ids": ["HGNC:12345", "HGNC:67890"]
        }
    Response: HTTP 200 with a message indicating no changes.

    Invalid request:
    >>> POST /compare-live-panelapp
    >>> {
            "existing_hgnc_ids": ["HGNC:12345", "HGNC:67890"]
        }
    Response: HTTP 400 with an error about missing clinical_id.
    """
    try:
        logging.info("Received request at /compare-live-panelapp")

        # Step 1: Extract and validate the input data from the request
        data = request.json
        if not data:
            logging.warning("Request data is missing or not in JSON format")
            return jsonify({"error": "Request must be in JSON format and contain 'clinical_id' and 'existing_hgnc_ids'"}), 400

        clinical_id = data.get("clinical_id")
        existing_hgnc_ids = data.get("existing_hgnc_ids")

        # Step 2: Validate the presence of clinical_id
        if not clinical_id:
            logging.warning("clinical_id is missing in the request data")
            return jsonify({"error": "Missing clinical_id"}), 400

        # Step 3: Validate the format of existing_hgnc_ids
        if not isinstance(existing_hgnc_ids, list):
            logging.warning(f"existing_hgnc_ids must be a list. Received: {type(existing_hgnc_ids)}")
            return jsonify({"error": "existing_hgnc_ids must be a list"}), 400

        logging.info(f"Comparing HGNC IDs for clinical_id: {clinical_id}. Existing HGNC IDs: {existing_hgnc_ids}")

        # Step 4: Retrieve live HGNC IDs from PanelApp
        try:
            live_hgnc_ids = get_hgnc_ids_for_r_code(clinical_id)  # Helper function to fetch live data
            logging.info(f"Retrieved live HGNC IDs for {clinical_id}: {live_hgnc_ids}")
        except Exception as retrieval_error:
            # Log and return an error if fetching live data fails
            logging.error(f"Error retrieving live HGNC IDs for {clinical_id}: {retrieval_error}")
            return jsonify({"error": f"Failed to retrieve live data for {clinical_id}: {str(retrieval_error)}"}), 500

        # Step 5: Compare the provided and live HGNC IDs
        existing_set = set(existing_hgnc_ids)  # Convert existing IDs to a set for comparison
        live_set = set(live_hgnc_ids)  # Convert live IDs to a set for comparison

        # Find differences
        added = list(live_set - existing_set)  # IDs in live data but not in existing data
        removed = list(existing_set - live_set)  # IDs in existing data but not in live data

        logging.debug(f"HGNC IDs added: {added}, removed: {removed}")

        # Step 6: Return the results of the comparison
        if not added and not removed:
            # If no differences are found, return a success message
            logging.info("No differences found between existing and live HGNC IDs.")
            return jsonify({"message": "No changes found. The live PanelApp data matches your current data."}), 200
        else:
            # If differences are found, return a detailed difference report
            difference_report = {
                "added": added,
                "removed": removed
            }
            logging.info("Differences found between existing and live HGNC IDs.")
            return jsonify({"message": "Differences found.", "differences": difference_report}), 200

    except Exception as e:
        # Log any unexpected errors and return a 500 error response
        logging.error(f"Unhandled error in /compare-live-panelapp route: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500
    
if __name__ == '__main__':
    """
    Main entry point for the Flask application.

    This block initializes logging, loads configuration settings, and starts the
    Flask application. It ensures that the application is configured correctly before
    running, and logs critical information for debugging and monitoring.

    Steps
    -----
    1. Initialize logging to capture application activity.
    2. Load the application configuration from a JSON file.
    3. Extract key configuration details for the application (e.g., database paths).
    4. Handle critical errors during configuration loading by logging and exiting.
    5. Start the Flask application in debug mode.

    Notes
    -----
    - The configuration file (`./config/app_config.json`) must exist and contain valid
      JSON data with the required keys: `patient_db_path`, `panel_dir`, and `r_code_file`.
    - Logging is configured via the `setup_logging()` function, which ensures that all
      activity is recorded to the appropriate logs and the console.
    - The application runs in debug mode for development purposes; this should be disabled
      in production environments.

    Examples
    --------
    Running the Flask application:
    >>> python app.py

    Expected console output (if configuration is valid):
    >>> INFO:root:Starting the Flask application setup...
    >>> INFO:root:Configuration loaded. Patient DB Path: /path/to/db, Panel Directory: /path/to/panel_dir
    >>> INFO:root:Starting Flask application...
    """
    # Step 1: Initialize logging to capture application activity
    setup_logging()  # Configure logging to capture INFO and ERROR messages
    logging.info("Starting the Flask application setup...")  # Log the startup process

    # Step 2: Load configuration from a JSON file
    try:
        # Load configuration from the specified path
        config = load_config("./configuration/app_config.json")  # Function reads and parses JSON

        # Extract key configuration variables
        patient_db_path = config["patient_db_path"]  # Path to the patient database
        panel_dir = config["panel_dir"]  # Directory containing PanelApp databases
        r_code_file = config["r_code_file"]  # File containing valid R codes

        # Log the loaded configuration details for debugging purposes
        logging.info(f"Configuration loaded. Patient DB Path: {patient_db_path}, Panel Directory: {panel_dir}")
    except Exception as e:
        # Log a critical error if configuration loading fails
        logging.critical(f"Failed to load configuration: {e}")

        # Exit the application with a non-zero status to indicate failure
        exit(1)  # Ensure the application does not start without valid configuration

    # Step 3: Start the Flask application
    logging.info("Starting Flask application...")  # Log the application startup process
    app.run(debug=True)  # Run the application in debug mode (development only)
