import os
import sqlite3
import pandas as pd
import argparse
import gzip
import shutil
import logging
from datetime import datetime
import requests
import tempfile

# Local module imports
from .build_panelApp_database import main as update_database
from .build_patient_database import save_to_database

def setup_logging():
    """
    Configure logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("retrieve_data.log"),
            logging.StreamHandler()
        ]
    )

def list_patients(patient_db):
    """
    List all patients in the patient database.

    Args:
        patient_db (str): Path to the patient database.
    """
    try:
        conn = sqlite3.connect(patient_db)  # Connect to the SQLite patient database
        query = "SELECT DISTINCT patient_id, clinical_id FROM patient_data"  # SQL query to get unique patient data
        df = pd.read_sql_query(query, conn)  # Fetch results into a DataFrame
        logging.info("Listing all patients and their clinical IDs:")
        logging.info(df)  # Log the results
    except Exception as e:
        logging.error(f"An error occurred while listing patients: {e}")  # Handle and log any errors
    finally:
        conn.close()  # Ensure the database connection is closed

def retrieve_latest_panelapp_db(archive_folder, panelapp_db):
    """
    Retrieve the latest PanelApp database from the working directory or archive folder.

    Args:
        archive_folder (str): Path to the archive folder.
        panelapp_db (str): Specific PanelApp database file to use. If not provided, the latest is used.

    Returns:
        tuple: Path to the PanelApp database and a flag indicating if it's a temporary file.
    """
    try:
        if panelapp_db:
            return panelapp_db, False  # If a specific database is provided, use it

        # Search for database files in the working directory
        db_files = [f for f in os.listdir() if f.startswith("panelapp_v") and f.endswith(".db")]
        if db_files:
            db_files.sort(reverse=True)  # Sort by name to find the latest
            return db_files[0], False  # Use the latest database file in the directory

        # If not found in the working directory, check the archive folder
        archived_files = [f for f in os.listdir(archive_folder) if f.startswith("panelapp_v") and f.endswith(".db.gz")]
        if archived_files:
            archived_files.sort(reverse=True)
            latest_archived = archived_files[0]

            # Extract the latest archived database
            temp_file = f"/tmp/{latest_archived.replace('.gz', '')}"  # Temporary file path
            with gzip.open(os.path.join(archive_folder, latest_archived), 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return temp_file, True  # Return the extracted database path and a flag
        raise FileNotFoundError("No PanelApp database found in the working directory or archive folder.")
    except Exception as e:
        logging.error(f"An error occurred while retrieving the PanelApp database: {e}")
        raise

def add_patient(patient_db, patient_id, clinical_id, test_date):
    """
    Add a new patient to the patient database.

    Args:
        patient_db (str): Path to the patient database.
        patient_id (str): Patient ID to add.
        clinical_id (str): Clinical ID associated with the patient.
        test_date (str): Test date in 'YYYY-MM-DD' format.
    """
    try:
        logging.info(f"Adding patient: {patient_id}, R code: {clinical_id}, Test date: {test_date}")

        # Find the latest `panelapp_v` database file in the working directory
        db_files = [f for f in os.listdir() if f.startswith("panelapp_v") and f.endswith(".db")]
        if not db_files:
            raise FileNotFoundError("No `panelapp_v` database found in the working directory.")

        db_files.sort(reverse=True)  # Sort files to find the latest version
        latest_file = db_files[0]  # Select the latest file

        # Extract version date from the filename
        version_date = latest_file.split("panelapp_v")[1].split(".")[0]
        panel_retrieved_date = f"{version_date[:4]}-{version_date[4:6]}-{version_date[6:]}"  # Format the version date

        # Create a DataFrame for the new patient data
        new_patient_data = [{
            "patient_id": patient_id,
            "clinical_id": clinical_id,
            "test_date": test_date,
            "panel_retrieved_date": panel_retrieved_date,
        }]
        patient_df = pd.DataFrame(new_patient_data)

        # Save the new patient data to the database
        save_to_database(patient_df, database_name=patient_db, table_name="patient_data")
        logging.info(f"Patient {patient_id} successfully added to the database.")
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"An error occurred while adding the patient: {e}")
        raise
def connect_and_join_databases(patient_db, panelapp_db, output_file, r_code=None, patient_id=None, archive_folder="archive_databases"):
    """
    Connects to the patient and PanelApp databases, joins them on clinical_id/relevant_disorders,
    and writes the resulting table to a CSV file. If panel_retrieved_date differs, retrieves the appropriate database.
    The table provides a gene list.

    Args:
        patient_db (str): Path to the patient database.
        panelapp_db (str): Path to the PanelApp database.
        output_file (str): Path to save the resulting table as CSV.
        r_code (str, optional): The R code (clinical_id) to filter and retrieve data for.
        patient_id (str, optional): The patient ID to filter and retrieve data for.
        archive_folder (str): Path to the archive folder containing older PanelApp databases.
    """
    try:
        # Connect to the patient database
        patient_conn = sqlite3.connect(patient_db)

        # Load patient data based on the provided filter (clinical_id or patient_id)
        patient_query = "SELECT * FROM patient_data"
        params = []
        if r_code:
            patient_query += " WHERE clinical_id = ?"
            params.append(r_code)
        elif patient_id:
            patient_query += " WHERE patient_id = ?"
            params.append(patient_id)

        patient_df = pd.read_sql_query(patient_query, patient_conn, params=params)  # Fetch patient data as a DataFrame

        if patient_df.empty:
            logging.warning("No matching patient data found.")
            return

        # Extract unique panel_retrieved_dates for joining with PanelApp data
        unique_dates = patient_df["panel_retrieved_date"].unique()

        # Initialize an empty DataFrame to store results
        result_df = pd.DataFrame()

        for date in unique_dates:
            # Build the file name for the PanelApp database based on the date
            panelapp_file = f"panelapp_v{date.replace('-', '')}.db"
            panelapp_path = os.path.join(os.getcwd(), panelapp_file)
            is_temp = False  # Flag to track if the file is temporary

            # Check if the PanelApp database exists, otherwise look in the archive
            if not os.path.isfile(panelapp_path):
                panelapp_path_gz = os.path.join(archive_folder, f"{panelapp_file}.gz")
                if os.path.isfile(panelapp_path_gz):
                    # Extract the database from the archive
                    with gzip.open(panelapp_path_gz, 'rb') as f_in:
                        with open(panelapp_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    logging.info(f"Unzipped archived database for date: {date}")
                    is_temp = True  # Mark the file as temporary
                else:
                    logging.error(f"No PanelApp database found for date: {date}")
                    continue

            # Connect to the PanelApp database
            try:
                panelapp_conn = sqlite3.connect(panelapp_path)

                # Load data from the PanelApp database
                panelapp_df = pd.read_sql_query("SELECT * FROM panel_info", panelapp_conn)

                # Join patient data with PanelApp data based on clinical_id/relevant_disorders
                patient_subset = patient_df[patient_df["panel_retrieved_date"] == date]
                joined_df = pd.merge(
                    patient_subset,
                    panelapp_df,
                    left_on="clinical_id",
                    right_on="relevant_disorders",
                    how="inner"
                )

                # Append the joined data to the results DataFrame
                result_df = pd.concat([result_df, joined_df], ignore_index=True)

            finally:
                # Close the PanelApp database connection
                panelapp_conn.close()

                # If a temporary file was created, delete it
                if is_temp:
                    try:
                        os.remove(panelapp_path)
                        logging.info(f"Deleted temporary database file: {panelapp_path}")
                    except Exception as delete_error:
                        logging.error(f"Failed to delete temporary database file {panelapp_path}: {delete_error}")

        if result_df.empty:
            logging.warning("No matching data found in PanelApp for the given criteria.")
            return

        # Save the joined data to a CSV file
        result_df.to_csv(output_file, index=False)
        logging.info(f"Joined table saved to {output_file}")
        logging.info(result_df.head())  # Log a preview of the result

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Ensure the patient database connection is closed
        patient_conn.close()

def get_panel_app_list():
    """
    Queries the PanelApp API to return details on all signed-off Panels.

    Returns:
        pd.DataFrame: DataFrame containing panel_id and version from the API.
    """
    server = "https://panelapp.genomicsengland.co.uk"
    ext = "/api/v1/panels/"

    r = requests.get(server + ext, headers={"Content-Type": "application/json"})

    # Handle API errors
    if not r.ok:
        r.raise_for_status()

    # Create the initial DataFrame from the API results
    panel_app_df = pd.json_normalize(r.json(), record_path=["results"])

    # List to store paginated results
    all_dataframes = [panel_app_df]

    # Follow pagination to fetch all data
    while r.json().get("next") is not None:
        r = requests.get(r.json()["next"], headers={"Content-Type": "application/json"})
        next_page_df = pd.json_normalize(r.json(), record_path=["results"])
        all_dataframes.append(next_page_df)

    # Combine all paginated results into one DataFrame
    panel_app_df = pd.concat(all_dataframes, ignore_index=True)

    # Select only id and version columns and rename them
    return panel_app_df[["id", "version"]].rename(columns={"id": "panel_id"})

def compare_panel_versions():
    """
    Compare panel versions between the latest local database in the working directory and the PanelApp API.

    Returns:
        None
    """
    try:
        # Find the latest PanelApp database in the working directory
        db_files = [f for f in os.listdir() if f.startswith("panelapp_v") and f.endswith(".db")]
        if not db_files:
            logging.error("No `panelapp_v` database found in the working directory.")
            return

        # Sort and select the latest version
        db_files.sort(reverse=True)
        latest_db = db_files[0]
        db_path = os.path.join(os.getcwd(), latest_db)

        logging.info(f"Using latest local PanelApp database: {latest_db}")

        # Connect to the local database and retrieve panel data
        conn = sqlite3.connect(db_path)
        local_df = pd.read_sql_query("SELECT panel_id, version FROM panel_info", conn)
        conn.close()

        logging.info("Retrieved panel data from the local database.")

        # Fetch the latest panel data from the API
        api_df = get_panel_app_list()
        logging.info("Retrieved panel data from the API.")

        # Compare local and API panel data
        merged_df = pd.merge(
            local_df,
            api_df,
            on="panel_id",
            how="outer",
            suffixes=("_local", "_api"),
            indicator=True
        )

        # Identify differences between the local database and the API
        differences = merged_df[merged_df["_merge"] != "both"]

        if not differences.empty:
            logging.warning("Differences found between local and API versions:")
            logging.warning(differences)
        else:
            logging.info("No differences found. Local database matches the API.")

    except Exception as e:
        logging.error(f"An error occurred during comparison: {e}")

def parse_arguments():
    """
    Parse command-line arguments for the script using subparsers.

    Returns:
        argparse.Namespace: Parsed arguments with selected command and options.
    """
    parser = argparse.ArgumentParser(
        description="PanelGeneMapper: A Tool for Integrating PanelApp Data with Lab Systems and Generating BED Files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands.")

    # Subparser for updating the database
    update_parser = subparsers.add_parser("update", help="Update the local PanelApp database.")

    # Subparser for listing patients
    list_parser = subparsers.add_parser("list_patients", help="List all patients in the database.")
    list_parser.add_argument("--patient_db", default="patient_database.db", help="Path to the patient database.")

    # Subparser for adding a patient
    add_patient_parser = subparsers.add_parser("add_patient", help="Add a new patient to the database.")
    add_patient_parser.add_argument("--patient_db", default="patient_database.db", help="Path to the patient database.")
    add_patient_parser.add_argument("--patient_id", required=True, help="Patient ID to add.")
    add_patient_parser.add_argument("--clinical_id", required=True, help="Clinical ID associated with the patient.")
    add_patient_parser.add_argument("--test_date", required=True, help="Test date in 'YYYY-MM-DD' format.")

    # Subparser for retrieving gene lists
    retrieve_genes_parser = subparsers.add_parser(
        "retrieve_genes", help="Retrieve gene lists for specific R codes or patient IDs."
    )
    retrieve_genes_parser.add_argument("--patient_db", default="patient_database.db", help="Path to the patient database.")
    retrieve_genes_parser.add_argument("--panelapp_db", help="Path to the PanelApp database.")
    retrieve_genes_parser.add_argument("--output_file", default="gene_list.csv", help="Path to save the resulting table.")
    retrieve_genes_parser.add_argument("--r_code", help="Filter by specific R code (clinical_id).")
    retrieve_genes_parser.add_argument("--patient_id", help="Filter by specific patient ID.")
    retrieve_genes_parser.add_argument("--archive_folder", default="archive_databases", help="Path to the archive folder.")

    # Subparser for comparing local database with API
    compare_parser = subparsers.add_parser(
        "compare_with_api", help="Compare the local PanelApp database with the latest API data."
    )

    return parser.parse_args()

def main():
    """
    Main function to parse arguments and execute the appropriate command.

    It orchestrates the script's behavior based on the command-line arguments.
    """
    # Set up logging configuration
    setup_logging()

    # Parse the command-line arguments
    args = parse_arguments()

    # Execute the appropriate command based on the parsed arguments
    if args.command == "update":
        try:
            update_database()  # Runs the update functionality from build_panelApp_database
            logging.info("Local PanelApp database updated successfully.")
        except Exception as e:
            logging.error(f"An error occurred while updating the database: {e}")

    elif args.command == "list_patients":
        # List all patients in the database
        list_patients(args.patient_db)

    elif args.command == "add_patient":
        # Add a new patient to the database
        add_patient(args.patient_db, args.patient_id, args.clinical_id, args.test_date)

    elif args.command == "retrieve_genes":
        try:
            # Retrieve the latest PanelApp database, creating a temporary file if necessary
            panelapp_db_path, is_temp = retrieve_latest_panelapp_db(args.archive_folder, args.panelapp_db)
            # Join patient and PanelApp databases and generate the gene list
            connect_and_join_databases(
                patient_db=args.patient_db,
                panelapp_db=panelapp_db_path,
                output_file=args.output_file,
                r_code=args.r_code,
                patient_id=args.patient_id,
                archive_folder=args.archive_folder,
            )
            # Delete temporary file if it was created
            if is_temp:
                os.remove(panelapp_db_path)
        except Exception as e:
            logging.error(f"An error occurred during gene retrieval: {e}")

    elif args.command == "compare_with_api":
        # Compare local database versions with PanelApp API data
        compare_panel_versions()

    else:
        # Log error for invalid command
        logging.error("Invalid command. Use --help to see available commands.")


if __name__ == "__main__":
    """
    Entry point for the script execution.
    Calls the `main` function to handle command-line arguments and commands.
    """
    main()
