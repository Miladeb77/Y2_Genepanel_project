import os
import sys
import logging
import time
import sqlite3

# Add the root directory to the Python path
root_dir= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

###############################
# Setup Logging
###############################

def setup_logging(info_log_file_path, error_log_file_path):
    """
    Configure logging for the application to record logs in two separate files 
    (one for INFO+ messages and another specifically for ERROR+ messages) 
    and also display all messages (INFO+) in the console.

    Parameters
    ----------
    info_log_file_path : str
        Path to the log file for recording all INFO-level (and above) messages.
    error_log_file_path : str
        Path to the log file for recording only ERROR-level (and above) messages.

    Notes
    -----
    - The root logger level is set to DEBUG to allow all messages to flow 
      through. Each handler then filters messages based on its configured 
      level.
    - A console handler is included to display INFO-level (and above) 
      messages in the terminal output.
    - The logger handlers are cleared first to avoid duplicating logs if 
      `setup_logging` is called multiple times.

    Examples
    --------
    Setting up logging with both an info log file and an error log file:
    >>> setup_logging("app.log", "app_error.log")
    """

    # Get or create the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  
    # Setting to DEBUG ensures all messages are processed; 
    # actual filtering happens in handlers.

    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a common format for all handlers
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # -----------------------------
    # 1. File Handler for INFO+
    # -----------------------------
    file_handler = logging.FileHandler(info_log_file_path)
    file_handler.setLevel(logging.INFO)  # Captures INFO and above
    file_handler.setFormatter(formatter)

    # -----------------------------
    # 2. Separate File Handler for ERROR+
    # -----------------------------
    error_file_handler = logging.FileHandler(error_log_file_path)
    error_file_handler.setLevel(logging.ERROR)  # Captures ERROR and above
    error_file_handler.setFormatter(formatter)

    # -----------------------------
    # 3. Console Handler for INFO+
    # -----------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Shows INFO and above on console
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    logging.info("Logging setup complete. INFO+ to file & console, ERROR+ to separate file.")

###############################
# Supporting Functions
###############################

def find_panelapp_directory(root_dir):
    """
    Search for a subdirectory within the given root directory that contains PanelApp database files.

    This function traverses all subdirectories under the specified root directory to locate
    a subdirectory containing files named with the prefix "panelapp_v" and the extension ".db".
    If no such subdirectory is found, a `FileNotFoundError` is raised.

    Parameters
    ----------
    root_dir : str
        The root directory to search for PanelApp database files.

    Returns
    -------
    str
        The path to the subdirectory containing PanelApp database files.

    Raises
    ------
    FileNotFoundError
        If no subdirectory within the root directory contains files matching the
        naming pattern "panelapp_v*.db".

    Notes
    -----
    - This function assumes that database files follow the naming convention "panelapp_v*.db".
    - If multiple subdirectories contain matching files, the first one encountered is returned.

    Examples
    --------
    Example usage:
    >>> find_panelapp_directory("/path/to/root")
    '/path/to/root/subdir_with_databases'

    If no database files are found:
    >>> find_panelapp_directory("/path/to/root")
    FileNotFoundError: No subdirectory in the root directory contains PanelApp database files (.db or .db.gz).
    """
    # Step 1: Traverse the root directory and its subdirectories
    # `os.walk` iterates through all subdirectories and files under `root_dir`
    for subdir, _, files in os.walk(root_dir):
        # Step 2: Check if any file in the current subdirectory matches the PanelApp naming pattern
        for file in files:
            # PanelApp database files must start with "panelapp_v" and end with ".db"
            if file.startswith("panelapp_v") and file.endswith(".db"):
                # Return the subdirectory path if a matching file is found
                return subdir

    # Step 3: Raise an error if no matching subdirectory is found after the traversal
    raise FileNotFoundError(
        "No subdirectory in the root directory contains PanelApp database files (.db or .db.gz)."
    )

def process_panelapp_directory(panelapp_dir: str, output_dir: str) -> tuple:
    """
    Process the PanelApp directory to identify and handle a new database file.

    This function scans the given `panelapp_dir` for a PanelApp database file that starts
    with "panelapp_v" and ends with ".db". It checks whether the database file has already
    been processed by comparing it to entries in a `processed_panelApp_versions.txt` file
    in the specified `output_dir`. If a new database file is found, it is added to the list
    of processed files, and its path is returned.

    Parameters
    ----------
    panelapp_dir : str
        Path to the PanelApp directory containing database files.
    output_dir : str
        Path to the output directory where the processed versions file is stored.

    Returns
    -------
    tuple
        A tuple containing:
        - str: The full path of the new database file if one is found, or `None` if no new file exists.
        - bool: `True` if a new unprocessed database file was found, otherwise `False`.

    Notes
    -----
    - A database file is considered "new" if it is not listed in the `processed_panelApp_versions.txt` file.
    - If the processed versions file does not exist, it is created automatically.

    Examples
    --------
    Process a directory with a new database:
    >>> process_panelapp_directory("/path/to/panelapp", "/path/to/output")
    ('/path/to/panelapp/panelapp_v20241219.db', True)

    Process a directory with no new databases:
    >>> process_panelapp_directory("/path/to/panelapp", "/path/to/output")
    (None, False)
    """
    # Ensure the output directory exists; create it if it does not
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Ensured output directory exists: {output_dir}")

    # Step 1: Path to the file storing processed database versions
    processed_file_path = os.path.join(output_dir, "processed_panelApp_versions.txt")

    # If the processed versions file does not exist, create an empty file
    if not os.path.exists(processed_file_path):
        with open(processed_file_path, "w") as f:
            pass  # Create an empty file
        logging.info(f"Created new processed versions file: {processed_file_path}")

    # Step 2: Search for a single PanelApp database file in the directory
    for file_name in os.listdir(panelapp_dir):
        if file_name.startswith("panelapp_v") and file_name.endswith(".db"):
            # Found a matching database file
            database_file = file_name
            database_path = os.path.join(panelapp_dir, database_file)
            break
    else:
        # If no matching database file is found, log a warning and return
        logging.warning("No PanelApp database files found in the directory.")
        return None, False

    # Step 3: Check if the found database file has already been processed
    new_unprocessed_file_found = True  # Flag indicating whether a new file is found
    with open(processed_file_path, "r+") as processed_file:
        # Read all previously processed file names into a set
        processed_versions = set(line.strip() for line in processed_file.readlines())

        if database_file not in processed_versions:
            # If the database file is new, add it to the processed versions list
            processed_file.write(f"{database_file}\n")
            logging.info(f"Added new database file to processed list: {database_file}")
            return database_path, new_unprocessed_file_found

    # Step 4: If the database file was already processed, update the flag
    new_unprocessed_file_found = False
    logging.info(f"Database file already processed: {database_file}")
    return None, new_unprocessed_file_found

def get_unique_relevant_disorders(db_path):
    """
    Extract unique values from the `relevant_disorders` field in the `panel_info` table of a database.

    This function connects to a SQLite database, retrieves all unique values from the
    `relevant_disorders` column in the `panel_info` table, and returns them as a list.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.

    Returns
    -------
    list of str
        A list of unique values from the `relevant_disorders` field.

    Raises
    ------
    Exception
        If there is an error connecting to the database or executing the query.

    Notes
    -----
    - The function assumes the `panel_info` table exists and contains a column named `relevant_disorders`.
    - The database connection is closed after the operation to avoid resource leaks.

    Examples
    --------
    Extract unique relevant disorders from a database:
    >>> get_unique_relevant_disorders("/path/to/database.db")
    ['Disorder_1', 'Disorder_2', 'Disorder_3']
    """
    try:
        # Step 1: Establish a connection to the SQLite database
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor object to execute SQL queries
        logging.info("Connected to the database.")  # Log successful connection

        # Step 2: Define and execute the SQL query to retrieve unique values
        query = "SELECT DISTINCT relevant_disorders FROM panel_info"  # SQL query to get unique values
        cursor.execute(query)  # Execute the query

        # Step 3: Fetch all unique values and store them in a list
        # - Each row returned by the query is a tuple, where the first element is the disorder
        unique_disorders = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found {len(unique_disorders)} unique disorders.")  # Log the count of unique disorders

        # Step 4: Close the database connection to free resources
        conn.close()
        logging.info("Database connection closed.")  # Log successful disconnection

        # Step 5: Return the list of unique disorders
        return unique_disorders

    except Exception as e:
        # Step 6: Handle and log any exceptions that occur during the operation
        logging.error(f"Error accessing the relevant_disorders field: {e}")  # Log the error
        raise  # Re-raise the exception to allow higher-level handling

def save_disorders_to_file(disorders, output_file):
    """
    Save a list of unique disorders to a text file.

    This function appends new disorders from the provided list to a text file. Before appending,
    it ensures that duplicate entries (already present in the file) are not added. If the file
    does not exist, it is created automatically.

    Parameters
    ----------
    disorders : list of str
        A list of disorder names to save to the file.
    output_file : str
        Path to the output file where the disorders will be saved.

    Raises
    ------
    Exception
        If an error occurs while reading, writing, or handling the file.

    Notes
    -----
    - The function ensures that duplicate entries are avoided by checking existing
      entries in the file.
    - The output file is opened in append mode, so new disorders are added without
      overwriting the existing content.

    Examples
    --------
    Save disorders to a file:
    >>> save_disorders_to_file(['Disorder_1', 'Disorder_2'], 'disorders.txt')

    If `disorders.txt` already contains 'Disorder_1':
    >>> save_disorders_to_file(['Disorder_1', 'Disorder_3'], 'disorders.txt')
    Only 'Disorder_3' is added to the file.

    """
    try:
        # Step 1: Check if the output file exists and read its contents
        # - If the file exists, read all existing entries into a set for fast lookups
        # - If the file does not exist, initialize an empty set
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                existing_disorders = set(line.strip() for line in f.readlines())  # Read and strip lines
        else:
            existing_disorders = set()  # Initialize an empty set if file does not exist

        # Step 2: Identify new disorders that are not already in the file
        # - Use a list comprehension to filter out disorders already in the set
        new_disorders = [disorder for disorder in disorders if disorder not in existing_disorders]

        # Step 3: Write new disorders to the file in append mode
        # - Open the file in append mode to add new entries without overwriting
        with open(output_file, "a") as f:
            for disorder in new_disorders:
                f.write(f"{disorder}\n")  # Write each new disorder followed by a newline

        # Step 4: Log the results
        # - Log the number of new disorders added or indicate if no new disorders were found
        if new_disorders:
            logging.info(f"Added {len(new_disorders)} new disorders to {output_file}.")
        else:
            logging.info("No new disorders to add.")  # Indicate that no new entries were added

    except Exception as e:
        # Step 5: Handle exceptions and log errors
        # - Log any error that occurs during the file read/write process
        logging.error(f"Error saving disorders to file: {e}")
        raise  # Re-raise the exception for higher-level handling

def main():
    """
    Main function to run the application. It performs the following tasks:
    1. Locates the PanelApp directory containing the database files.
    2. Ensures the necessary directories for logs and output exist.
    3. Sets up logging, including separate files for INFO+ and ERROR+ levels,
       and console output for all INFO+ messages.
    4. Processes the PanelApp directory to identify any new database file.
    5. Extracts unique relevant disorders from the identified database and appends them
       to an output text file, avoiding duplicates.

    Raises
    ------
    FileNotFoundError
        If the PanelApp directory or database files cannot be located.
    OSError
        If directories cannot be created due to permissions or other filesystem issues.
    RuntimeError
        If logging setup fails for any reason.
    Exception
        For any other unexpected errors.

    Examples
    --------
    To execute the program directly:
    >>> main()

    Typical log output:
    INFO: Attempting to locate the PanelApp directory.
    INFO: PanelApp directory located at: /path/to/panelapp
    INFO: Directories created or already exist: /path/to/logs, /path/to/output
    INFO: Logging initialized.
    INFO: Successfully processed new database and appended unique disorders.
    """
    try:
        # Step 1: Locate the PanelApp directory
        logging.info("Attempting to locate the PanelApp directory.")
        panelapp_dir = find_panelapp_directory(root_dir)  # Locate the PanelApp directory
        if not panelapp_dir:
            # Raise an error if the directory cannot be located
            raise FileNotFoundError("PanelApp directory could not be located. Ensure the root directory is correct.")
        logging.info(f"PanelApp directory located at: {panelapp_dir}")

        # Step 2: Create necessary directories for logs and output
        # Define paths for logs and output directories
        logs_dir = os.path.join(root_dir, "logs")
        valid_rcodes_output_dir = os.path.join(root_dir, "output")
        try:
            # Create directories if they do not already exist
            os.makedirs(logs_dir, exist_ok=True)
            os.makedirs(valid_rcodes_output_dir, exist_ok=True)
            logging.info(f"Directories created or already exist: {logs_dir}, {valid_rcodes_output_dir}")
        except Exception as e:
            # Raise an error if directory creation fails
            raise OSError(f"Failed to create directories for logs or output: {e}")

        # Step 3: Set up logging
        # Define the log file path
        info_log_file_path = os.path.join(logs_dir, "generate_valid_rcode_list.log")
        error_log_file_path = os.path.join(logs_dir, "generate_valid_rcode_list_error.log")
        try:
            # Initialize logging configuration
            
            setup_logging(info_log_file_path, error_log_file_path)
            logging.info(f"Logging initialized.")
        except Exception as e:
            # Raise an error if logging setup fails
            raise RuntimeError(f"Failed to set up logging: {e}")

        # Step 4: Define output file for storing unique disorders
        valid_rcodes_output_file = os.path.join(valid_rcodes_output_dir, "unique_relevant_disorders.txt")

        # Step 5: Process the PanelApp directory to find new database files
        database_path, new_unprocessed_file_found = process_panelapp_directory(panelapp_dir, valid_rcodes_output_dir)

        # Step 6: Extract and save unique disorders if a new unprocessed file is found
        if new_unprocessed_file_found and database_path is not None:
            # Extract unique relevant disorders from the identified database
            unique_disorders = get_unique_relevant_disorders(db_path=database_path)

            # Save the unique disorders to the output file, avoiding duplicates
            save_disorders_to_file(disorders=unique_disorders, output_file=valid_rcodes_output_file)
            logging.info("Successfully processed new database and appended unique disorders.")

    except FileNotFoundError as e:
        # Log a file not found error
        logging.error(str(e))
    except OSError as e:
        # Log an operating system error (e.g., directory creation issues)
        logging.error(str(e))
    except RuntimeError as e:
        # Log a runtime error (e.g., logging setup failure)
        logging.error(str(e))
    except Exception as e:
        # Log any other unexpected errors
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    """
    Entry point for the application.

    This block runs the `main` function in an infinite loop, pausing for 2 minutes
    (120 seconds) between successive executions. The program continuously processes
    the PanelApp directory, updating logs and output files with any new data.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    - This implementation ensures the process runs indefinitely, making it suitable
      for long-running applications that require periodic updates.
    - The `time.sleep` function is used to introduce a delay of 2678400 seconds
      between iterations.
    - If `main` raises an unhandled exception, the loop will terminate. To ensure
      continuous operation, consider wrapping `main` with a try-except block
      to log errors and resume execution.

    Examples
    --------
    Running the script:
    $ python script.py
    """
    # Step 1: Start an infinite loop
    # - This ensures the `main` function runs continuously without manual intervention.
    while True:
        # Step 2: Execute the `main` function
        # - This processes the PanelApp directory and handles all required operations.
        main()

        # Step 3:
        # - Use `time.sleep` to introduce a delay between successive executions.
        # - This prevents excessive resource usage and allows periodic updates.
        time.sleep(2678400)  # Wait for 1 month before the next iteration
