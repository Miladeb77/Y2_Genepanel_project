import pandas as pd
import random
from datetime import datetime, timedelta
import sqlite3
import logging
import os
import sys
import argparse

# Add the directory containing custom_logging to sys.path
script_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(script_dir)

from custom_logging import setup_logging


def load_patient_data(databases_dir, patient_data_file):
    """
    Load patient data from a JSON file in the databases directory.

    Args:
        databases_dir (str): Path to the databases directory.
        patient_data_file (str): Name of the JSON file containing patient data.

    Returns:
        list: List of patient data dictionaries if the file exists, else None.
    """
    if not patient_data_file:
        logging.info("No patient data file specified. Using generated data.")
        return None

    patient_data_path = os.path.join(databases_dir, patient_data_file)
    if os.path.exists(patient_data_path):
        logging.info(f"Loading patient data from {patient_data_path}")
        try:
            with open(patient_data_path, "r") as file:
                data = pd.read_json(file).to_dict(orient="records")

                # Validate required fields
                for record in data:
                    if not all(key in record for key in ["patient_id", "clinical_id", "test_date"]):
                        raise ValueError(f"Invalid record in patient data: {record}")

                return data
        except ValueError as ve:
            logging.error(f"Validation error in patient data: {ve}")
            raise
        except Exception as e:
            logging.error(f"Failed to load patient data from {patient_data_path}: {e}")
            raise
    else:
        logging.info(f"No patient data file found at {patient_data_path}. Using generated data.")
        return None


def generate_patient_database(num_patients, patient_data, clinical_ids=None, default_test_date=None):
    """
    Generate a patient database with options for user-defined data.
    """
    # Set the panel retrieved date to the current date.
    panel_retrieved_date = datetime.now().strftime("%Y-%m-%d")
# If user-provided patient data is available, use it to generate the database.
    if clinical_ids is None:
        clinical_ids = ['R169', 'R419', 'R56', 'R60', 'R62', 'R58', 'R233', 'R39', 'R293', 'R106', 'R330',
                        'R340', 'R414', 'R446', 'R133', 'R83', 'R295', 'R201', 'R19', 'R155', 'R413',
                        'R167', 'R422', 'R107', 'R391', 'R49.3', 'R31', 'R90', 'R43', 'R128', 'R337',
                        'R319', 'R156', 'R129', 'R333', 'R87', 'R336', 'R57', 'R61', 'R109', 'R359', 'R171',
                        'R415', 'R124', 'R123', 'R99', 'R229, R258', 'R180', 'R150', 'R46', 'R144', 'R145',
                        'R79', 'R80', 'R81', 'R262', 'R237', 'R184', 'R193', 'R334', 'R91', 'R449', 'R450',
                        'R451', 'R364', 'R146', 'R132', 'R73', 'R59', 'R163', 'R101', 'R140', 'R217',
                        'R255', 'R164', 'R335', 'R345', 'R112', 'R118', 'R115', 'R116', 'R117', 'R119',
                        'R120', 'R122', 'R324', 'R329', 'R134', 'R151', 'R153', 'R254', 'R358', 'R162',
                        'R221', 'R21, R412', 'R365', 'R272', 'R384', 'R142', 'R274', 'R273', 'R288',
                        'R194', 'R361', 'R232', 'R18', 'R436', 'R341', 'R55, R84', 'R54', 'R215', 'R405',
                        'R186', 'R440', 'R78', 'R204', 'R177', 'R85', 'R86', 'R182', 'R131', 'R148', 'R154',
                        'R69', 'R165', 'R239', 'R208', 'R210', 'R207', 'R367', 'R226', 'R223', 'R211',
                        'R347', 'R363', 'R430', 'R224', 'R366', 'R29', 'R331', 'R157', 'R96', 'R280',
                        'R281', 'R139', 'R41.3, R42.1', 'R216', 'R98', 'R82', 'R158', 'R127', 'R17',
                        'R325', 'R276', 'R371', 'R197', 'R396', 'R353', 'R354', 'R355', 'R356', 'R357',
                        'R352', 'R317', 'R394', 'R338', 'R141', 'R67', 'R453', 'R327', 'R289', 'R277',
                        'R278', 'R291', 'R292', 'R287', 'R290', 'R417.2', 'R218', 'R390', 'R230', 'R351',
                        'R143', 'R143.1', 'R256', 'R222', 'R231', 'R271', 'R313', 'R214', 'R444', 'R282',
                        'R380', 'R259.2', 'R168', 'R41', 'R102', 'R104.4', 'R381', 'R27', 'R135', 'R438',
                        'R166', 'R175', 'R66', 'R212', 'R283', 'R236', 'R159', 'R190', 'R315', 'R173',
                        'R63', 'R344', 'R15', 'R136', 'R160', 'R328', 'R195', 'R420', 'R213', 'R426',
                        'R188', 'R421', 'R316', 'R92', 'R332', 'R100', 'R198', 'R189', 'R32', 'R219',
                        'R285', 'R235', 'R376', 'R110', 'R16', 'R234', 'R149', 'R88', 'R130', 'R52', 'R323',
                        'R104', 'R76', 'R270', 'R71', 'R38', 'R45', 'R36', 'R424', 'R138, R425', 'R192',
                        'R416', 'R286', 'R93', 'R25', 'R395', 'R125', 'R406', 'R97', 'R228', 'R202', 'R441',
                        'R257', 'R284', 'R170', 'R326', 'R225', 'R121', 'R220', 'R172', 'R20', 'R227']

    patients = []
# If user-provided patient data is available, use it to generate the database.
    if patient_data:
        logging.info("Using user-provided patient data.")
        for record in patient_data:
            # Use provided data or generate defaults for missing fields.
            patient_id = record.get("patient_id", f"Patient_{random.randint(10000000, 99999999)}")
            clinical_id = record.get("clinical_id", random.choice(clinical_ids))
            test_date = record.get("test_date", default_test_date)
            # Add the patient record to the list.
            patients.append({
                "patient_id": patient_id,
                "clinical_id": clinical_id,
                "test_date": test_date,
                "panel_retrieved_date": panel_retrieved_date,
            })
    # If no user-provided data, generate random patient data.
    else:
        logging.info("Generating random patient data.")
        for _ in range(num_patients):
            # Generate a random patient ID.
            patient_id = f"Patient_{random.randint(10000000, 99999999)}"
            # Randomly select a clinical ID from the list.
            clinical_id = random.choice(clinical_ids)
            start_of_year = datetime(datetime.now().year, 1, 1)
            random_days = random.randint(0, (datetime.now() - start_of_year).days)
            test_date = (start_of_year + timedelta(days=random_days)).strftime("%Y-%m-%d")
            patients.append({
                "patient_id": patient_id,
                "clinical_id": clinical_id,
                "test_date": test_date,
                "panel_retrieved_date": panel_retrieved_date,
            })

    patient_df = pd.DataFrame(patients)
    logging.info("Patient database generated successfully.")
    return patient_df


def save_to_database(df, databases_dir, database_name, table_name="patient_data"):
    """
    Save the DataFrame to an SQLite database in the databases directory.
    """
    try:
        # Ensure the databases directory exists
        os.makedirs(databases_dir, exist_ok=True)

        # Path for the database
        database_path = os.path.join(databases_dir, database_name)

        # Save data to the database
        conn = sqlite3.connect(database_path)
        logging.info(f"Connected to database '{database_path}'.")

        # Append the data to the table
        df.to_sql(table_name, conn, if_exists="append", index=False)

        logging.info(f"Data successfully added to table '{table_name}' in '{database_path}'.")
        conn.close()
        logging.info("Database connection closed.")
    except Exception as e:
        logging.error(f"An error occurred while saving to the database: {e}")
        raise


def parse_arguments():
    """
    Parse command-line arguments for generating the patient database.
    """
    # Create an argument parser for handling command-line input.
    parser = argparse.ArgumentParser(description="Generate a patient database.")

    # Argument for specifying the number of patient records to generate.
    # Defaults to 500 if not provided by the user.
    parser.add_argument(
        "--num_patients",
        type=int,
        default=500,
        help="Number of patient records to generate (default: 500)."
    )

    # Argument for providing a JSON file containing patient data.
    # If not specified, patient data will be generated programmatically.
    parser.add_argument(
        "--patient_data_file",
        type=str,
        default=None,
        help="JSON file containing patient data (optional)."
    )

    # Argument for specifying the name of the SQLite database file.
    # Defaults to 'patient_database.db' if not provided.
    parser.add_argument(
        "--database_name",
        type=str,
        default="patient_database.db",
        help="Name of the SQLite database file (default: patient_database.db)."
    )

    # Argument for setting a default test date for the generated patients.
    # If not provided, the test date will be randomly generated or left unset.
    parser.add_argument(
        "--default_test_date",
        type=str,
        default=None,
        help="Default test date in 'YYYY-MM-DD' format for generated patients."
    )

    # Parse the command-line arguments and return the parsed values.
    return parser.parse_args()



def main():
    """
    Main function to generate and store the patient database.
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Define directories
        script_dir = os.path.abspath(os.path.dirname(__file__))
        project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
        logs_dir = os.path.join(project_dir, "logs")
        databases_dir = os.path.join(project_dir, "databases")

        # Set up centralized logging using custom_logging
        setup_logging(
            logs_dir=logs_dir,
            info_log_file="build_patient_info.log",
            error_log_file="build_patient_error.log"
        )

        logging.info("Patient database script started.")

        # Load patient data if provided
        patient_data = load_patient_data(databases_dir, args.patient_data_file)

        # Generate the patient database
        patient_df = generate_patient_database(
            num_patients=args.num_patients,
            patient_data=patient_data,
            default_test_date=args.default_test_date
        )

        # Save to SQLite database
        save_to_database(patient_df, databases_dir=databases_dir, database_name=args.database_name)

        logging.info("Patient database script completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred in the patient database script: {e}")
        raise


if __name__ == "__main__":
    main()

