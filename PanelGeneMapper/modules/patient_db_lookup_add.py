import os
import logging
import sqlite3
import pandas as pd


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


def list_patients(patient_db="patient_database.db", save_to_file=False):
    """
    List all patients in the patient database and optionally save the list to a CSV file.

    Args:
        patient_db (str): Name of the patient database file.
        save_to_file (bool): Whether to save the patient list to a CSV file.
    """
    databases_dir = get_databases_dir()
    patient_db_path = os.path.join(databases_dir, patient_db)
    conn = None

    try:
        if not os.path.isfile(patient_db_path):
            logging.error(f"Patient database not found at {patient_db_path}.")
            return

        conn = sqlite3.connect(patient_db_path)
        query = "SELECT DISTINCT patient_id, clinical_id FROM patient_data"
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logging.info("No patients found in the database.")
        else:
            logging.info("Listing all patients and their clinical IDs:")
            logging.info(df)

            if save_to_file:
                output_dir = os.path.join(databases_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, "patient_list.csv")
                df.to_csv(output_path, index=False)
                logging.info(f"Patient list saved to {output_path}")

    except sqlite3.Error as e:
        logging.error(f"An error occurred while listing patients: {e}")
    finally:
        if conn:
            conn.close()


def add_patient(patient_id, clinical_id, test_date):
    """
    Add a new patient to the patient database.

    Args:
        patient_id (str): Patient ID to add.
        clinical_id (str): Clinical ID associated with the patient.
        test_date (str): Test date in 'YYYY-MM-DD' format.
    """
    try:
        databases_dir = get_databases_dir()
        patient_db = os.path.join(databases_dir, "patient_database.db")

        logging.info(f"Adding patient: {patient_id}, R code: {clinical_id}, Test date: {test_date}")

        with sqlite3.connect(patient_db) as conn:
            existing_patients = pd.read_sql_query("SELECT patient_id FROM patient_data", conn)

        if patient_id in existing_patients["patient_id"].values:
            logging.warning(
                f"Patient {patient_id} already exists in the database. Patient was not added."
            )
            return

        db_files = [
            f for f in os.listdir(databases_dir) if f.startswith("panelapp_v") and f.endswith(".db")
        ]
        if not db_files:
            raise FileNotFoundError(
                f"No `panelapp_v` database found in the databases directory: {databases_dir}"
            )

        db_files.sort(reverse=True)
        latest_file = os.path.join(databases_dir, db_files[0])

        version_date = latest_file.split("panelapp_v")[1].split(".")[0]
        panel_retrieved_date = f"{version_date[:4]}-{version_date[4:6]}-{version_date[6:]}"

        new_patient_data = [
            {
                "patient_id": patient_id,
                "clinical_id": clinical_id,
                "test_date": test_date,
                "panel_retrieved_date": panel_retrieved_date,
            }
        ]
        patient_df = pd.DataFrame(new_patient_data)

        save_to_database(patient_df, databases_dir, database_name="patient_database.db")
        logging.info(f"Patient {patient_id} successfully added to the database.")

    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"An error occurred while adding the patient: {e}")
        raise


def save_to_database(df, databases_dir, database_name="patient_database.db", table_name="patient_data"):
    """
    Save the DataFrame to an SQLite database in the databases directory.

    Args:
        df (pd.DataFrame): DataFrame to save.
        databases_dir (str): Path to the databases directory.
        database_name (str): Name of the SQLite database file.
        table_name (str): Name of the table in the database.
    """
    try:
        database_path = os.path.join(databases_dir, database_name)
        os.makedirs(databases_dir, exist_ok=True)

        if not os.path.isfile(database_path):
            logging.error(f"Database file not found at {database_path}.")
            raise FileNotFoundError(f"Database file not found at {database_path}.")

        with sqlite3.connect(database_path) as conn:
            logging.info(f"Connected to database '{database_path}'.")
            df.to_sql(table_name, conn, if_exists="append", index=False)
            logging.info(
                f"Data successfully added to table '{table_name}' in '{database_path}'."
            )

    except Exception as e:
        logging.error(f"An error occurred while saving to the database: {e}")
        raise


if __name__ == "__main__":
    databases_dir = get_databases_dir()
    patient_db = os.path.join(databases_dir, "patient_database.db")
