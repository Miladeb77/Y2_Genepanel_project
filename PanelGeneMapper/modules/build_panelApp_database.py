import requests
import pandas as pd
import json
import sqlite3
import os
import logging
from datetime import datetime
import gzip
from tempfile import NamedTemporaryFile
import re

def set_working_directory():
    """
    Set the working directory to the location of the script.
    
    Returns:
        str: The directory path where the script is located.
    
    Raises:
        OSError: If changing the directory fails.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logging.info(f"Setting working directory to the script's location: {script_dir}")
        os.chdir(script_dir)
        logging.info("Working directory successfully set.")
        return script_dir
    except OSError as e:
        logging.error(f"Failed to set working directory: {e}")
        raise

def setup_logging(script_dir, info_log_file="build_panelApp_db_info_log.log", error_log_file="build_panelApp_db_error_log.log"):
    """
    Configure logging settings for the script, directing output to separate files for INFO and ERROR levels.
    
    Args:
        script_dir (str): The directory path where the script is located.
        info_log_file (str): The file name for INFO level logging output.
        error_log_file (str): The file name for ERROR level logging output.
        
    Logs:
        Info-level message that logging has started.
    """
    # Set log file paths relative to the provided script directory
    info_log_path = os.path.join(script_dir, info_log_file)
    error_log_path = os.path.join(script_dir, error_log_file)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the root logger level to DEBUG to capture all messages

    # Remove existing handlers to avoid duplicate logs or conflicts
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Logger for INFO and above messages
    info_handler = logging.FileHandler(info_log_path)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(info_handler)

    # Logger for ERROR and above messages
    error_handler = logging.FileHandler(error_log_path)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(error_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    logging.info("Logging setup complete.")

def load_config(config_file="build_panelApp_database_config.json"):
    """
    Load configuration settings from a JSON file.
    
    Args:
        config_file (str): Path to the configuration file.
    
    Returns:
        dict: Configuration settings loaded from the file.
    
    Raises:
        FileNotFoundError: If the configuration file is not found.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    try:
        # Get the path to the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the configuration file
        config_path = os.path.join(script_dir, "..", "config", config_file)
        logging.info(f"Attempting to load configuration from {config_file}")
        with open(config_file, "r") as f:
            config = json.load(f)
        logging.info("Configuration successfully loaded.")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Configuration file is not in valid JSON format.")
        raise

def initialize_api(config):
    """
    Initialize API constants using the configuration settings.
    
    Args:
        config (dict): Configuration settings.
    
    Returns:
        tuple: A tuple containing the panels URL (str) and headers (dict).
    
    Raises:
        KeyError: If essential configuration keys are missing.
    """
    try:
        logging.info("Initializing API constants from configuration.")
        
        server = config.get("server")
        if server:
            logging.info(f"API server set to: {server}")
        else:
            logging.error("Missing 'server' key in configuration.")
            raise KeyError("server")
        
        panels_url = f"{server}/api/v1/panels/"
        logging.info(f"API panels URL initialized as: {panels_url}")
        
        headers = config.get("headers")
        if headers:
            logging.info("API headers successfully loaded.")
        else:
            logging.error("Missing 'headers' key in configuration.")
            raise KeyError("headers")
        
        return panels_url, headers
    
    except KeyError as e:
        logging.error(f"Initialization failed due to missing configuration key: {e}")
        raise

def fetch_panels(panels_url, headers):
    """
    Fetch all panels with relevant disorders starting with 'R'.
    
    Args:
        panels_url (str): The base URL for fetching panels.
        headers (dict): Headers required for the API request.
    
    Returns:
        list: A list of panel data dictionaries.
    
    Logs:
        Errors encountered during requests and final retrieval count.
    """
    all_panels = []
    page = 1
    
    logging.info("Starting to fetch panels with relevant disorders.")
    
    while True:
        try:
            if page % 10 == 0:
                logging.info(f"Fetching page {page} of panels.")
            else:
                logging.debug(f"Fetching page {page} of panels.")

            response = requests.get(panels_url, headers=headers, params={"page": page})
            
            if response.status_code == 200 and response.headers.get("Content-Type") == "application/json":
                data = response.json()
                panels = data.get("results", [])
                all_panels.extend(panels)
                logging.debug(f"Retrieved {len(panels)} panels from page {page}.")
                
                if data.get("next") is None:
                    logging.info("No more pages to fetch.")
                    break
                page += 1
            else:
                logging.error(f"Failed to retrieve data on page {page}. Status code: {response.status_code} or unexpected content type.")
                break
                
        except requests.RequestException as e:
            logging.error(f"Request to fetch panels failed on page {page}: {e}")
            break

    logging.info(f"Finished fetching panels. Total panels retrieved: {len(all_panels)}")
    return all_panels

def fetch_panel_details(panel_id, panels_url, headers):
    """
    Fetch detailed panel and gene information for a specific panel by ID.
    
    Args:
        panel_id (str): The unique identifier for the panel.
        panels_url (str): The base URL for panels.
        headers (dict): Headers required for the API request.
    
    Returns:
        dict: Detailed information for the specified panel, or None if retrieval fails.
    
    Logs:
        Debug-level success or failure of each request.
    """
    panel_detail_url = f"{panels_url}{panel_id}/"
    
    logging.debug(f"Fetching details for panel ID: {panel_id}")
    
    try:
        response = requests.get(panel_detail_url, headers=headers)
        
        if response.status_code == 200 and response.headers.get("Content-Type") == "application/json":
            logging.debug(f"Successfully retrieved details for panel ID: {panel_id}")
            return response.json()
        else:
            logging.error(f"Failed to retrieve details for panel ID: {panel_id}. "
                          f"Status code: {response.status_code} or unexpected content type.")
            return None
            
    except requests.RequestException as e:
        logging.error(f"Request failed while fetching details for panel ID: {panel_id}. Error: {e}")
        return None

def process_panel_data(panels, panels_url, headers):
    """
    Process panel data to extract and format relevant information.

    Args:
        panels (list): List of panel data dictionaries.
        panels_url (str): The base URL for panels.
        headers (dict): Headers required for the API request.

    Returns:
        list: A list of dictionaries, each containing detailed panel and gene data.

    Logs:
        Progress every 20% of panels processed, and a single "100%" completion message.
    """
    all_panel_gene_data = []
    total_panels = len(panels)
    logging.info("Starting to process panel data.")
    logging.info(f"Total panels to process: {total_panels}")

    # Calculate the increment threshold for logging
    progress_threshold = max(1, total_panels // 5)  # Log every 20%, ensure at least every panel for small datasets

    for i, panel in enumerate(panels, start=1):
        # Process relevant disorders
        r_codes = [disorder for disorder in panel.get("relevant_disorders", []) if re.match(r"R\d+(\.\d+)?", disorder)]
        if not r_codes:
            continue  # Skip panels without relevant disorders

        # Fetch panel details
        panel_details = fetch_panel_details(panel["id"], panels_url, headers)
        if not panel_details:
            continue  # Skip if details retrieval failed

        # Construct panel and gene data
        panel_info = {
            "panel_id": panel_details["id"],
            "hash_id": panel_details.get("hash_id"),
            "name": panel_details["name"],
            "disease_group": panel_details.get("disease_group", ""),
            "disease_sub_group": panel_details.get("disease_sub_group", ""),
            "status": panel_details["status"],
            "version": panel_details["version"],
            "version_created": (
                datetime.strptime(panel_details["version_created"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
                if "version_created" in panel_details and panel_details["version_created"]
                else None),
            "relevant_disorders": r_codes,
            "number_of_genes": panel_details["stats"].get("number_of_genes", 0),
            "number_of_strs": panel_details["stats"].get("number_of_strs", 0),
            "number_of_regions": panel_details["stats"].get("number_of_regions", 0),
            "panel_type": ", ".join([name.split(",")[-1].strip() for name in [ptype.get("name", "") for ptype in panel_details.get("types", [])]]),
            }
        
        for gene in panel_details.get("genes", []):
            gene_data = gene.get("gene_data", {})
            ensembl_data = gene_data.get("ensembl_genes", {})
            grch38_data = ensembl_data.get("GRch38", {}).get("90", {}) if isinstance(ensembl_data, dict) else {}
            gene_entry = {
                "gene_symbol": gene_data.get("gene_symbol"),
                "hgnc_symbol": gene_data.get("hgnc_symbol"),
                "mode_of_pathogenicity": gene.get("mode_of_pathogenicity"),
                "phenotypes": gene.get("phenotypes", []),
                "mode_of_inheritance": gene.get("mode_of_inheritance"),
                "transcript": gene_data.get("transcript"),
                "hgnc_id": gene_data.get("hgnc_id"),
                "evidence": gene.get("evidence", []),
                "gene_ensembl_id_GRch38": grch38_data.get("ensembl_id"),
                }
            combined_data = {**panel_info, **gene_entry}
            all_panel_gene_data.append(combined_data)


        # Log progress every 20%
        if i % progress_threshold == 0:
            logging.info(f"Processed {i}/{total_panels} panels ({(i / total_panels) * 100:.0f}%)")

    logging.info("Completed processing all panel data.")
    return all_panel_gene_data

def format_data(data):
    """
    Format data into a DataFrame for database insertion.
    
    Args:
        data (list): List of dictionaries containing panel and gene information.
    
    Returns:
        pd.DataFrame: A DataFrame formatted for database insertion.
    
    Logs:
        Progress and completion of the formatting process.
    """
    try:
        logging.info("Starting to format data for database insertion.")
        
        df = pd.DataFrame(data)
        logging.info(f"Data loaded into DataFrame with {len(df)} rows and {len(df.columns)} columns.")
        
        list_columns = ["relevant_disorders", "publications", "evidence", "phenotypes", "transcript"]
        
        for col in list_columns:
            if col in df.columns:
                logging.info(f"Formatting list column '{col}' into comma-separated strings.")
                df[col] = df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else "")
            else:
                logging.warning(f"Column '{col}' not found in DataFrame.")
        
        if "types" in df.columns:
            logging.info("Formatting 'types' column by converting dictionaries to JSON strings.")
            df["types"] = df["types"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else "")
        else:
            logging.warning("Column 'types' not found in DataFrame.")
        
        for col in df.columns:
            if df[col].dtype == "object":
                logging.info(f"Converting column '{col}' to string data type.")
                df[col] = df[col].astype(str)
        
        logging.info("Data formatting completed successfully.")
        return df

    except Exception as e:
        logging.error(f"An error occurred during data formatting: {e}")
        raise

def save_to_database(df, script_dir, table_name="panel_info"):
    """
    Save the DataFrame to an SQLite database, with old database files archived.
    
    Args:
        df (pd.DataFrame): The DataFrame containing the data to be saved.
        script_dir (str): The directory path for saving the database.
        table_name (str): The name of the table in the database.
    
    Raises:
        sqlite3.DatabaseError: If there is a database error during saving.
        OSError: If there is an issue with file handling or compression.
    
    Logs:
        Progress and completion of the save and archive processes.
    """
    try:
        if df.empty:
            logging.warning("No data to save. The DataFrame is empty.")
            return
        
        logging.info("Starting to save data to the SQLite database.")
        
        date_str = datetime.now().strftime("%Y%m%d")
        database_name = f"panelapp_v{date_str}.db"
        logging.info(f"Database name set to: {database_name}")

        archive_folder = os.path.join(script_dir, "archive_databases")
        os.makedirs(archive_folder, exist_ok=True)
        logging.info(f"Archive folder located at: {archive_folder}")

        files_in_directory = os.listdir(script_dir)
        if any(db_file.startswith("panelapp_v") and db_file.endswith(".db") and db_file != database_name for db_file in files_in_directory):
            for db_file in files_in_directory:
                if db_file.startswith("panelapp_v") and db_file.endswith(".db") and db_file != database_name:
                    old_db_path = os.path.join(script_dir, db_file)
                    archived_db_path = os.path.join(archive_folder, db_file)
                    
                    os.rename(old_db_path, archived_db_path)
                    with open(archived_db_path, 'rb') as f_in, gzip.open(f"{archived_db_path}.gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                    os.remove(archived_db_path)
            logging.info("Archived and compressed old database files.")

        conn = sqlite3.connect(database_name)
        logging.info(f"Connected to database '{database_name}'")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        logging.info(f"Data successfully saved to table '{table_name}' in '{database_name}'")
        
        conn.close()
        logging.info(f"Database connection to '{database_name}' closed.")
        
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error occurred while saving data: {e}")
        raise
    except OSError as e:
        logging.error(f"File operation error during database save process: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving data to the database: {e}")
        raise

def main():
    """
    Main function to initialize environment, retrieve and process data, and save it to the database.
    
    Logs:
        Any errors occurring during script execution.
    """

    # Temporary logging setup
    temp_log_file = NamedTemporaryFile(delete=False, suffix=".log").name
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(temp_log_file), logging.StreamHandler()]
    )
    logging.info("Temporary logging setup complete.")

    try:
        # Set the working directory and get the script directory
        script_dir = set_working_directory()

        # Pass the script directory to setup_logging
        setup_logging(script_dir)

        # Merge temporary logs into the main log file
        with open(temp_log_file, 'r') as temp_log:
            temp_log_contents = temp_log.read()
            logging.info("---- Temporary Logs Start ----\n" + temp_log_contents + "---- Temporary Logs End ----")

        # Remove the temporary log file
        os.remove(temp_log_file)

        # Load configuration and initialize the API
        config = load_config()
        panels_url, headers = initialize_api(config)

        # Fetch, process, and save data
        panels = fetch_panels(panels_url, headers)
        panel_gene_data = process_panel_data(panels, panels_url, headers)
        formatted_df = format_data(panel_gene_data)
        save_to_database(formatted_df, script_dir)

        logging.info("Script completed successfully.")
    
    except Exception as e:
        logging.error(f"An error occurred during script execution: {e}")
        raise

# Run the main function if this file is executed
if __name__ == "__main__":
    main()