

### Consider the importance of the fact that where (from which directory) the user runs this program ### 

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import logging
from datetime import datetime
import gzip
import shutil
from multiprocessing import Pool
from filelock import FileLock

# Initialize the Flask app and specify the static folder for serving files
app = Flask(__name__, static_folder='static')

def setup_logging():
    """
    Set up logging for the application. Creates a log directory and configures
    separate logs for info and error messages, along with console output.
    """
    LOG_DIR = "./app_logs"  # Define the directory for logs
    os.makedirs(LOG_DIR, exist_ok=True)  # Create the logs directory if it doesn't already exist

    # Paths for log files
    info_log_path = os.path.join(LOG_DIR, "info_log.log")
    error_log_path = os.path.join(LOG_DIR, "error_log.log")

    # Create handlers
    info_handler = logging.FileHandler(info_log_path, mode="a")
    info_handler.setLevel(logging.INFO)  # Capture all INFO and higher messages

    error_handler = logging.FileHandler(error_log_path, mode="a")
    error_handler.setLevel(logging.ERROR)  # Capture only ERROR and higher messages

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show DEBUG and higher messages on the console

    # Define the log message format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Add the formatter to the handlers
    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set the base logging level
        handlers=[info_handler, error_handler, console_handler]  # Add all handlers
    )

    logging.info("Logging has been set up successfully.")  # Log that logging has been initialized

# Helper Functions

def decompress_if_needed(file_path):
    """
    Decompress a .gz file if it exists and return the path to the decompressed version.
    If the file is not compressed, return the original path.

    Args:
        file_path (str): Path to the file (compressed or uncompressed).

    Returns:
        str: Path to the decompressed or original file.

    Raises:
        ValueError: If the decompressed file is empty.
        Exception: For any other issues during decompression.
    """
    try:
        if file_path.endswith('.gz'):  # Check if the file is compressed
            decompressed_file = file_path[:-3]  # Generate the decompressed file path
            lock_file = f"{decompressed_file}.lock"  # Create a lock file for decompression

            logging.info(f"Preparing to decompress file: {file_path}")

            # Use a file lock to prevent race conditions
            with FileLock(lock_file):
                # Only decompress if the decompressed file doesn't exist or is empty
                if not os.path.exists(decompressed_file) or os.path.getsize(decompressed_file) == 0:
                    logging.info(f"Decompressing file: {file_path} -> {decompressed_file}")
                    with gzip.open(file_path, 'rb') as f_in, open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                    # Verify that the decompressed file is not empty
                    if os.path.getsize(decompressed_file) == 0:
                        raise ValueError(f"Decompressed file is empty: {decompressed_file}")

                else:
                    logging.info(f"Decompressed file already exists and is valid: {decompressed_file}")

            return decompressed_file  # Return the path to the decompressed file

        # If not compressed, return the original path
        return file_path

    except Exception as e:
        logging.error(f"Error while decompressing {file_path}: {e}")
        raise  # Raise the exception to handle it upstream

def find_relevant_panel_db(panel_retrieved_date, root_dir):
    """
    Search for the PanelApp database corresponding to a specific date.

    Args:
        panel_retrieved_date (str): Date in 'YYYY-MM-DD' format.
        root_dir (str): The directory containing the PanelApp databases.

    Returns:
        str: Path to the matching PanelApp database.

    Raises:
        FileNotFoundError: If no database matching the date is found.
    """
    try:
        # Convert the date format into the expected file prefix (e.g., "20241119")
        target_prefix = f"panelapp_v{panel_retrieved_date.replace('-', '')}"
        logging.info(f"Searching for PanelApp database with prefix: {target_prefix}")
        # Recursively search through the directory and its subdirectories
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if file.startswith(target_prefix):  # Check if the file matches the prefix
                    logging.info(f"Found relevant database: {file}")
                    return os.path.join(dirpath, file)  # Return the full file path
        # If no match is found, raise an exception
        raise FileNotFoundError(f"No PanelApp database found for date {panel_retrieved_date}.")
    except FileNotFoundError as e:
        logging.error(e)
        raise  # Re-raise the exception to indicate failure

def find_most_recent_panel_db(root_dir):
    """
    Find the most recent uncompressed PanelApp database in the specified directory.

    Args:
        root_dir (str): The directory containing the PanelApp databases.

    Returns:
        str: Path to the most recent uncompressed PanelApp database.

    Raises:
        FileNotFoundError: If no uncompressed database is found.
    """
    try:
        most_recent_db = None  # Initialize the path of the most recent database
        most_recent_time = None  # Initialize the timestamp of the most recent database
        # Traverse all files in the root directory
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if file.endswith(".db"):  # Only consider uncompressed database files
                    file_path = os.path.join(dirpath, file)  # Get the full file path
                    creation_time = os.path.getctime(file_path)  # Get the file creation timestamp
                    # Check if the current file is more recent than the stored one
                    if most_recent_time is None or creation_time > most_recent_time:
                        most_recent_db = file_path
                        most_recent_time = creation_time
        # If no database is found, raise an exception
        if not most_recent_db:
            raise FileNotFoundError("No uncompressed PanelApp database found.")
        logging.info(f"Most recent PanelApp database: {most_recent_db}")
        return most_recent_db  # Return the path to the most recent database
    except Exception as e:
        logging.error(e)
        raise  # Re-raise the exception to indicate failure

def find_most_recent_panel_date(root_dir):
    """
    Extract the date from the most recent PanelApp database.

    Args:
        root_dir (str): The directory containing the PanelApp databases.

    Returns:
        str: Date in 'YYYY-MM-DD' format.

    Raises:
        Exception: If the database or its date cannot be processed.
    """
    try:
        # Find the most recent database file
        most_recent_db = find_most_recent_panel_db(root_dir)
        base_name = os.path.basename(most_recent_db)  # Extract the file name
        date_str = base_name.split("_v")[1].split("_")[0]  # Extract the date string
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"  # Format as 'YYYY-MM-DD'
        logging.info(f"Most recent PanelApp database date: {formatted_date}")
        return formatted_date  # Return the formatted date
    except Exception as e:
        logging.error(e)
        raise

def extract_genes_from_panel(db_path, r_code):
    """
    Extract a list of distinct gene symbols associated with a specific R code.

    Args:
        db_path (str): Path to the PanelApp database.
        r_code (str): The R code for which genes are being retrieved.

    Returns:
        list: A list of gene symbols.

    Raises:
        Exception: If there is an issue reading the database.
    """
    decompressed = False  # Track whether the database was decompressed
    original_path = db_path
    db_path = decompress_if_needed(db_path)  # Decompress if needed
    if db_path != original_path:
        decompressed = True  # Mark as decompressed

    try:
        logging.info(f"Extracting genes for R code: {r_code} from {db_path}")
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Query the gene_data table to find relevant gene symbols
        cursor.execute("SELECT DISTINCT gene_symbol FROM gene_data WHERE relevant_disorders LIKE ?", (f"%{r_code}%",))
        genes = [row[0] for row in cursor.fetchall()]  # Fetch all results
        conn.close()  # Close the database connection
        logging.info(f"Genes found for R code {r_code}: {genes}")
        return genes
    finally:
        # Only delete the file if there are no remaining locks
        if decompressed and not os.path.exists(f"{db_path}.lock"):
            os.remove(db_path)
            logging.info(f"Deleted decompressed file: {db_path}")

def get_patient_data(patient_id, db_path):
    """
    Fetch all records associated with a specific patient ID from the database.

    Args:
        patient_id (str): The unique identifier of the patient to search for.
        db_path (str): Path to the SQLite database file.

    Returns:
        list: A list of tuples, where each tuple represents a record from the `patients` table.

    Raises:
        Exception: If there is an error querying the database.
    """
    try:
        logging.info(f"Fetching data for patient ID: {patient_id}")  # Log the patient ID being fetched
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor to execute SQL commands
        # Query to fetch all records for the specified patient ID
        cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        records = cursor.fetchall()  # Fetch all matching rows
        conn.close()  # Close the database connection
        logging.info(f"Records fetched for patient ID {patient_id}: {records}")  # Log the fetched records
        return records
    except Exception as e:
        logging.error(f"Error fetching data for patient ID {patient_id}: {e}")  # Log any errors encountered
        raise  # Raise the exception to be handled by the calling function

def add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, db_path):
    """
    Add a new patient record to the `patients` table in the database.

    Args:
        patient_id (str): The unique identifier of the patient.
        r_code (str): The relevant disorder (R Code) associated with the patient.
        inserted_date (str): The timestamp when the record is inserted (format: 'YYYY-MM-DD HH:MM:SS').
        panel_retrieved_date (str): The date associated with the PanelApp database (format: 'YYYY-MM-DD').
        db_path (str): Path to the SQLite database file.

    Raises:
        Exception: If there is an error inserting the record into the database.
    """
    try:
        logging.info(f"Adding new patient record: {patient_id}, R code: {r_code}, Panel Retrieved Date: {panel_retrieved_date}")
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor to execute SQL commands
        # Insert the new record into the `patients` table
        cursor.execute("""
            INSERT INTO patients (patient_id, relevant_disorders, inserted_date, panel_retrieved_date)
            VALUES (?, ?, ?, ?)
        """, (patient_id, r_code, inserted_date, panel_retrieved_date))
        conn.commit()  # Commit the changes to the database
        conn.close()  # Close the database connection
        logging.info(f"Successfully added patient record: {patient_id}")  # Log the successful insertion
    except Exception as e:
        logging.error(f"Error adding patient record {patient_id}: {e}")  # Log any errors encountered
        raise  # Raise the exception to be handled by the calling function

def process_patient_record(record, panel_dir):
    """
    Process a single patient record to retrieve its gene panel from the corresponding PanelApp database.

    Args:
        record (tuple): A single record from the `patients` table, containing:
                        - patient_id (str): The unique identifier of the patient.
                        - relevant_disorders (str): The R code associated with the patient.
                        - inserted_date (str): The timestamp when the record was inserted.
                        - panel_retrieved_date (str): The date to locate the appropriate PanelApp database.
        panel_dir (str): Path to the directory containing the PanelApp databases.

    Returns:
        dict: A dictionary containing:
              - patient_id (str): The unique identifier of the patient.
              - relevant_disorders (str): The R code associated with the patient.
              - inserted_date (str): The timestamp when the record was inserted.
              - panel_retrieved_date (str): The date of the associated PanelApp database.
              - gene_panel (list): A list of genes related to the R code.

    Steps:
        1. Extract relevant fields from the record.
        2. Locate the appropriate PanelApp database using `find_relevant_panel_db`.
        3. Retrieve the gene panel for the R code using `extract_genes_from_panel`.
        4. Return the data in a structured dictionary.
    """
    try:
        # Extract relevant fields from the record tuple
        patient_id, r_code, inserted_date, panel_retrieved_date = record[1:]  # Skip the primary key

        # Locate the PanelApp database for the given retrieval date
        logging.info(f"Locating database for Panel Retrieved Date: {panel_retrieved_date}")
        panel_db_path = find_relevant_panel_db(panel_retrieved_date, panel_dir)

        # Retrieve the gene panel for the specified R code
        logging.info(f"Fetching gene panel for R code {r_code} from {panel_db_path}")
        gene_panel = extract_genes_from_panel(panel_db_path, r_code)

        # Return the patient data along with the retrieved gene panel
        return {
            "patient_id": patient_id,
            "relevant_disorders": r_code,
            "inserted_date": inserted_date,
            "panel_retrieved_date": panel_retrieved_date,
            "gene_panel": gene_panel
        }
    except Exception as e:
        logging.error(f"Error processing patient record {record}: {e}")  # Log any error during processing
        raise  # Re-raise the exception for higher-level handling

def get_r_code_data(r_code, db_path):
    """
    Fetch all patient records from the `patients` table associated with a given R code.

    Args:
        r_code (str): The R code to search for in the `relevant_disorders` field.
        db_path (str): Path to the SQLite database containing the `patients` table.

    Returns:
        list: A list of tuples, where each tuple represents a matching record from the `patients` table.

    Steps:
        1. Connect to the SQLite database.
        2. Use a parameterized SQL query to find records where `relevant_disorders` contains the R code.
        3. Fetch all matching rows.
        4. Close the database connection.
        5. Return the results as a list of tuples.
    """
    try:
        logging.info(f"Fetching records for R code: {r_code} from database: {db_path}")  # Log the search operation
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor to execute SQL commands

        # SQL query to find all records matching the R code (use parameterized query to avoid SQL injection)
        query = "SELECT * FROM patients WHERE relevant_disorders = ?"
        cursor.execute(query, (r_code,))  # Include wildcards to match partial values

        # Fetch all matching rows from the query
        records = cursor.fetchall()
        conn.close()  # Close the database connection
        logging.info(f"Records fetched for R code {r_code}: {records}")  # Log the retrieved records
        return records
    except Exception as e:
        logging.error(f"Error fetching records for R code {r_code}: {e}")  # Log any error encountered
        raise  # Re-raise the exception for higher-level handling

@app.route('/')
def index():
    """
    Serve the `index.html` file for the root URL.

    This is the main entry point of the application, providing the user interface.

    Returns:
        Response: The `index.html` file from the static folder.
    """
    logging.info("Serving index.html for the root route.")  # Log when the index page is served
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    logging.info(f"Serving static file: {filename}")
    return send_from_directory(app.static_folder, filename)

@app.route('/patient', methods=['GET'])
def fetch_patient_data():
    """
    Handle GET requests to check for patient data and prompt for an R Code if the patient doesn't exist.
    """
    try:
        # Get the patient ID from the query parameters
        patient_id = request.args.get('patient_id')

        if not patient_id:
            logging.warning("Patient ID is missing in the request.")
            return jsonify({"error": "Patient ID is required."}), 400

        # Path to the patient database
        patient_db_path = "./Patient_db/patient_database.db"

        # Search for the patient ID in the database
        records = get_patient_data(patient_id, patient_db_path)

        if not records:
            logging.info(f"No records found for Patient ID: {patient_id}")
            return jsonify({
                "message": f"No records found for Patient ID '{patient_id}'. Please provide an R Code to create a new record.",
                "prompt": "Please provide the R Code for this patient to create a new record."
            }), 404

        # If records exist, process them and include gene panel information
        panel_dir = "./PanelApp_extract_data"
        with Pool() as pool:
            results = pool.starmap(process_patient_record, [(record, panel_dir) for record in records])

        logging.debug(f"Processed data for Patient ID {patient_id}: {results}")
        return jsonify(results), 200

    except Exception as e:
        logging.error(f"Error in /patient GET route: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/patient/add', methods=['POST'])
def add_patient_record_with_rcode():
    """
    Handle POST requests to add a new patient record using the provided patient ID and R Code.
    """
    try:
        # Get the patient ID and R Code from the request body
        data = request.json
        patient_id = data.get('patient_id')
        r_code = data.get('r_code')

        if not patient_id or not r_code:
            logging.warning("Missing Patient ID or R Code in the request.")
            return jsonify({"error": "Both Patient ID and R Code are required."}), 400

        # Paths to the databases
        patient_db_path = "./Patient_db/patient_database.db"
        panel_dir = "./PanelApp_extract_data"

        # Add the new patient record
        inserted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        panel_retrieved_date = find_most_recent_panel_date(panel_dir)
        add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, patient_db_path)

        # Retrieve the gene panel for the new record
        panel_db_path = find_most_recent_panel_db(panel_dir)
        gene_panel = extract_genes_from_panel(panel_db_path, r_code) or []

        logging.info(f"New patient record created for ID {patient_id} with R code {r_code}")
        return jsonify({
            "message": "New patient record created successfully.",
            "patient_id": patient_id,
            "relevant_disorders": r_code,
            "inserted_date": inserted_date,
            "panel_retrieved_date": panel_retrieved_date,
            "gene_panel": gene_panel
        }), 201

    except Exception as e:
        logging.error(f"Error in /patient/add POST route: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/rcode', methods=['GET'])
def fetch_rcode_data():
    """
    Handle requests for R Code searches.
    - If the R Code exists, return records.
    - If the R Code does not exist, prompt the user and handle responses accordingly.
    """
    try:
        r_code = request.args.get('r_code')  # Get the R Code from query parameters
        if not r_code:
            logging.warning("R code is missing in the request.")
            return jsonify({"error": "R code is required."}), 400

        # Paths to the databases
        patient_db_path = "./Patient_db/patient_database.db"
        panel_dir = "./PanelApp_extract_data"

        # Fetch all records associated with the R Code
        records = get_r_code_data(r_code, patient_db_path)
        if not records:
            # If no records found, provide a structured response
            logging.info(f"No records found for R code: {r_code}")
            return jsonify({
                "message": f"R code '{r_code}' not found.",
                "rcode": r_code,
                "prompt": "No patients have had this R code analysis. Do you have any patients that have had an analysis with this R code? Reply 'Yes' or 'No'."
            }), 404

        # If records are found, process them
        with Pool() as pool:  # Use multiprocessing for parallel processing
            results = pool.starmap(process_patient_record, [(record, panel_dir) for record in records])
        return jsonify(results), 200

    except Exception as e:
        logging.error(f"Error in /rcode route: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/rcode/handle', methods=['POST'])
def handle_rcode():
    """
    Handle the user's response to the 'R code not found' prompt.
    """
    try:
        user_response = request.json.get('response')  # Get user's response
        r_code = request.json.get('r_code')  # R Code provided earlier

        if not r_code or not user_response:
            logging.warning("Missing R code or user response in the request.")
            return jsonify({"error": "R code and user response are required."}), 400

        if user_response.lower() == "no":
            # If the user says no, return to the main page
            logging.info(f"User indicated no patients exist for the R code: {r_code}.")
            return jsonify({"message": "No action taken. Returning to main page."}), 200

        if user_response.lower() == "yes":
            # If the user says yes, process patient IDs
            patient_ids = request.json.get('patient_ids')  # Expect a list of patient IDs
            if not patient_ids:
                logging.warning("No patient IDs provided for new record creation.")
                return jsonify({"error": "Please provide a list of patient IDs."}), 400

            # Use the most recent PanelApp database
            panel_dir = "./PanelApp_extract_data"
            panel_retrieved_date = find_most_recent_panel_date(panel_dir)
            panel_db_path = find_most_recent_panel_db(panel_dir)

            # Add new records for each patient
            patient_db_path = "./Patient_db/patient_database.db"
            inserted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_records = []

            for patient_id in patient_ids:
                # Add the new patient record
                add_patient_record(patient_id, r_code, inserted_date, panel_retrieved_date, patient_db_path)

                # Retrieve the gene panel for the new record
                gene_panel = extract_genes_from_panel(panel_db_path, r_code)
                new_records.append({
                    "patient_id": patient_id,
                    "relevant_disorders": r_code,
                    "inserted_date": inserted_date,
                    "panel_retrieved_date": panel_retrieved_date,
                    "gene_panel": gene_panel
                })

            logging.info(f"New records created for R code {r_code} and patients: {patient_ids}")
            return jsonify({
                "message": "New records created successfully.",
                "new_records": new_records
            }), 201

        # Handle unexpected responses
        logging.warning(f"Unexpected response: {user_response}")
        return jsonify({"error": "Invalid response. Please reply 'Yes' or 'No'."}), 400

    except Exception as e:
        logging.error(f"Error in /rcode/handle route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    setup_logging()  # Initialize logging
    logging.info("Starting the Flask application...")  # Log application startup
    app.run(debug=True)  # Start the Flask application