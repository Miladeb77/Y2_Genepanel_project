import os
import logging
import sqlite3
import pandas as pd
import shutil
import gzip


def get_databases_dir():
    """
    Get the path to the databases directory two levels up from the script location.
    Ensures the directory exists.

    Returns:
        str: Path to the databases directory.
    """
    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    databases_dir = os.path.join(project_dir, "databases")
    os.makedirs(databases_dir, exist_ok=True)
    return databases_dir


def get_archive_dir():
    """
    Get the path to the archive_databases directory two levels up from the script location.
    Ensures the directory exists.

    Returns:
        str: Path to the archive_databases directory.
    """
    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    databases_dir = os.path.join(project_dir, "databases")
    archive_dir = os.path.join(databases_dir, "archive_databases")
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
        db_files = [
            f for f in os.listdir(databases_dir)
            if f.startswith("panelapp_v") and f.endswith(".db")
        ]
        if db_files:
            db_files.sort(reverse=True)
            return os.path.join(databases_dir, db_files[0]), False

        # Check for the latest database in the archive folder
        archived_files = [
            f for f in os.listdir(archive_dir)
            if f.startswith("panelapp_v") and f.endswith(".db.gz")
        ]
        if archived_files:
            archived_files.sort(reverse=True)
            latest_archived = archived_files[0]

            temp_file = f"/tmp/{latest_archived.replace('.gz', '')}"
            with gzip.open(os.path.join(archive_folder, latest_archived), "rb") as f_in:
                with open(temp_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            return temp_file, True

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
    specific_date=None,
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
        archive_folder (str, optional): Path to the archive folder.
        specific_date (str, optional): Process only the specified panel_retrieved_date (e.g., '2024-12-20').
    """
    try:
        if not os.path.isfile(patient_db):
            raise FileNotFoundError(f"Patient database not found: {patient_db}")

        patient_conn = sqlite3.connect(patient_db)

        # Construct patient query
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

        # Filter dates if a specific date is provided
        unique_dates = patient_df["panel_retrieved_date"].unique()
        if specific_date:
            unique_dates = [d for d in unique_dates if d == specific_date]
            if not unique_dates:
                logging.warning(f"No data found for specific date: {specific_date}")
                return

        result_df = pd.DataFrame()
        for date in unique_dates:
            panelapp_file = f"panelapp_v{date.replace('-', '')}.db"
            panelapp_path = os.path.join(get_databases_dir(), panelapp_file)
            panelapp_path_gz = os.path.join(get_archive_dir(), f"{panelapp_file}.gz")
            is_temp = False

            if os.path.isfile(panelapp_path_gz):
                with gzip.open(panelapp_path_gz, "rb") as f_in:
                    with open(panelapp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                is_temp = True

            if not os.path.isfile(panelapp_path):
                logging.error(f"No PanelApp database found for date: {date}")
                continue

            try:
                with sqlite3.connect(panelapp_path) as panelapp_conn:
                    panelapp_df = pd.read_sql_query("SELECT * FROM panel_info", panelapp_conn)

                patient_subset = patient_df[patient_df["panel_retrieved_date"] == date]
                joined_df = pd.merge(
                    patient_subset,
                    panelapp_df,
                    left_on="clinical_id",
                    right_on="relevant_disorders",
                    how="inner",
                )
                result_df = pd.concat([result_df, joined_df], ignore_index=True)
            finally:
                if is_temp:
                    os.remove(panelapp_path)

        if result_df.empty:
            logging.warning("No matching data found in PanelApp for the given criteria.")
            return

        result_df = result_df.rename(columns={
            "name": "disease_name",
            "relevant_disorders": "panel_r_code"
        })[[
            "patient_id", "clinical_id", "test_date", "panel_retrieved_date",
            "disease_name", "version", "version_created", "panel_r_code",
            "hgnc_symbol", "hgnc_id", "gene_ensembl_id_GRch38"
        ]]

        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        result_df.to_csv(output_file, index=False)
        logging.info(f"Joined table saved to {output_file}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
