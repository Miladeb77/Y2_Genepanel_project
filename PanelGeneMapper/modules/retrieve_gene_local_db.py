import sqlite3
import logging
import os
import pandas as pd
import shutil
import gzip


def get_databases_dir():
    """
    Get the path to the databases directory two levels up from the script location.
    Ensures the directory exists.
    """
    # Get the absolute path of the directory where the script is located.
    script_dir = os.path.abspath(os.path.dirname(__file__))
    # Navigate two levels up from the script directory to reach the project directory.
    project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    # Construct the path to the "databases" directory within the project directory.
    databases_dir = os.path.join(project_dir, "databases")
    # Create the "databases" directory if it doesn't already exist.
    os.makedirs(databases_dir, exist_ok=True)
    # Return the absolute path to the "databases" directory.
    return databases_dir

def get_archive_dir():
    """
    Get the path to the archive_databases directory two levels up from the script location.
    Ensures the directory exists.
    """
    # Get the absolute path of the directory where the script is located.
    script_dir = os.path.abspath(os.path.dirname(__file__))
    # Navigate two levels up from the script directory to reach the project directory.
    project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    # Construct the path to the "databases" directory within the project directory.
    databases_dir = os.path.join(project_dir, "databases")
    # Construct the path to the "archive_databases" directory inside the "databases" directory.
    archive_dir = os.path.join(databases_dir, "archive_databases")
    # Create the "archive_databases" directory if it doesn't already exist.
    os.makedirs(archive_dir, exist_ok=True)
    return archive_dir



def retrieve_latest_panelapp_db(archive_folder=None, panelapp_db=None):
    """
    Retrieve the latest PanelApp database from the databases directory or archive folder.

    Args:
        archive_folder (str, optional): Path to the archive folder. If not provided, it uses the default.
        panelapp_db (str, optional): Specific PanelApp database file to use. If not provided, the latest is used.

    Returns:
        tuple: Path to the PanelApp database and a flag indicating if it's a temporary file.
    """
    try:
        databases_dir = get_databases_dir()
        archive_dir = get_archive_dir()
        
        if panelapp_db and os.path.isfile(panelapp_db):
            return panelapp_db, False

        # Check for the latest database in the databases directory
        db_files = [f for f in os.listdir(databases_dir) if f.startswith("panelapp_v") and f.endswith(".db")]
        if db_files:
            db_files.sort(reverse=True)  # Latest file based on name
            return os.path.join(databases_dir, db_files[0]), False

        # If no database found, check the archive folder
        if archive_dir:
            archived_files = [
                f for f in os.listdir(archive_dir) if f.startswith("panelapp_v") and f.endswith(".db.gz")
            ]
            if archived_files:
                archived_files.sort(reverse=True)
                latest_archived = archived_files[0]

                # Extract the latest archived file
                temp_file =  f"/tmp/{latest_archived.replace('.gz', '')}"
                with gzip.open(os.path.join(archive_folder, latest_archived), 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                return temp_file, True  # Temporary file extracted

        raise FileNotFoundError("No PanelApp database found in the databases or archive folder.")

    except Exception as e:
        logging.error(f"An error occurred while retrieving the PanelApp database: {e}")
        raise



def connect_and_join_databases(
    patient_db,
    panelapp_db=None,
    output_file="output/gene_list.csv",
    r_code=None,
    patient_id=None,
    archive_folder=None,
    specific_date=None,  # Optional: Process a specific date only
):
    """
    Connects to the patient and PanelApp databases, joins them on clinical_id/relevant_disorders,
    and writes the resulting table to a CSV file.

    Args:
        patient_db (str): Path to the patient database.
        panelapp_db (str, optional): Path to the PanelApp database. If not provided, it retrieves the latest.
        output_file (str): Path to save the resulting table as CSV.
        r_code (str, optional): The R code (clinical_id) to filter and retrieve data for.
        patient_id (str, optional): The patient ID to filter and retrieve data for.
        archive_folder (str, optional): Path to the archive folder. If not provided, defaults to the archive folder in the project directory.
        specific_date (str, optional): Process only the specified panel_retrieved_date (e.g., '2024-12-20').
    """
    try:
        databases_dir = get_databases_dir()
        archive_dir = get_archive_dir()

        # Ensure the patient database exists
        if not os.path.isfile(patient_db):
            raise FileNotFoundError(f"Patient database not found: {patient_db}")

        # Connect to the patient database
        patient_conn = sqlite3.connect(patient_db)

        # Load patient data based on the provided filter
        patient_query = "SELECT * FROM patient_data"
        params = []
        if r_code:
            patient_query += " WHERE clinical_id = ?"
            params.append(r_code)
        elif patient_id:
            patient_query += " WHERE patient_id = ?"
            params.append(patient_id)

        patient_df = pd.read_sql_query(patient_query, patient_conn, params=params)

        if patient_df.empty:
            logging.warning("No matching patient data found.")
            return

        # Check for unique panel_retrieved_dates
        unique_dates = patient_df["panel_retrieved_date"].unique()

        # Filter dates if a specific date is provided
        if specific_date:
            unique_dates = [d for d in unique_dates if d == specific_date]
            if not unique_dates:
                logging.warning(f"No data found for specific date: {specific_date}")
                return

        # Initialize an empty DataFrame for results
        result_df = pd.DataFrame()

        for date in unique_dates:
            logging.info(f"Processing panel_retrieved_date: {date}")
            # Determine the appropriate database file for the date
            panelapp_file = f"panelapp_v{date.replace('-', '')}.db"
            panelapp_path = os.path.join(databases_dir, panelapp_file)
            panelapp_path_gz = os.path.join(archive_folder, f"{panelapp_file}.gz")
            is_temp = False

            # Check if the database exists
            if os.path.isfile(panelapp_path):
                logging.info(f"Using existing database file for date: {date} in databases directory.")
            elif os.path.isfile(panelapp_path_gz):
                with gzip.open(panelapp_path_gz, 'rb') as f_in:
                    with open(panelapp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                logging.info(f"Unzipped archived database for date: {date}")
                is_temp = True
            else:
                logging.error(f"No PanelApp database found for date: {date}")
                continue

            # Process the database
            try:
                logging.info(f"Processing database for date: {date}")
                panelapp_conn = sqlite3.connect(panelapp_path)
                panelapp_df = pd.read_sql_query("SELECT * FROM panel_info", panelapp_conn)

                # Filter patient data for the current date
                patient_subset = patient_df[patient_df["panel_retrieved_date"] == date]
                joined_df = pd.merge(
                    patient_subset,
                    panelapp_df,
                    left_on="clinical_id",
                    right_on="relevant_disorders",
                    how="inner"
                )
                result_df = pd.concat([result_df, joined_df], ignore_index=True)
            finally:
                panelapp_conn.close()

            # Only delete the temporary file after processing
            if is_temp:
                try:
                    os.remove(panelapp_path)
                    logging.info(f"Deleted temporary database file for date {date}: {panelapp_path}")
                except Exception as delete_error:
                    logging.error(f"Failed to delete temporary database file for date {date}: {delete_error}")

        if result_df.empty:
            logging.warning("No matching data found in PanelApp for the given criteria.")
            return

        # Select only the required columns
        result_df = result_df.rename(columns={
            "name": "disease_name",
            "relevant_disorders": "panel_r_code"
        })[
            [
                "patient_id",
                "clinical_id",
                "test_date",
                "panel_retrieved_date",
                "disease_name",
                "version",
                "version_created",
                "panel_r_code",
                "hgnc_symbol",
                "hgnc_id",
                "gene_ensembl_id_GRch38",
            ]
        ]

        # Adjust output path based on provided filters
        script_dir = os.path.abspath(os.path.dirname(__file__))
        project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
        output_dir = os.path.join(project_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "gene_list.csv")

        # Save the resulting table to a CSV file
        result_df.to_csv(output_path, index=False)
        logging.info(f"Joined table saved to {output_path}")
        logging.info(result_df.head())

    except Exception as e:
        logging.error(f"An error occurred: {e}")