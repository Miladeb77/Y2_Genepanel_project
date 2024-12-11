import pandas as pd
import random
from datetime import datetime, timedelta
import argparse
import json
import sqlite3
import logging
import os

def setup_logging():
    """
    Configure logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("patient_build_database.log"),
            logging.StreamHandler()
        ]
    )

def generate_patient_database(num_patients=500, patient_data=None, clinical_ids=None, default_test_date=None):
    """
    Generate a patient database with options for user-defined data.
    
    Args:
        num_patients (int): Number of patient records to generate if no patient data is provided.
        patient_data (list of dict): List of dictionaries containing user-defined patient data.
        clinical_ids (list): List of clinical IDs to randomly select from if not provided in patient_data.
        default_test_date (str): Default test date in 'YYYY-MM-DD' format if not provided in patient_data.

    Returns:
        pd.DataFrame: DataFrame containing the patient database.
    """
    # Find the latest `panelapp_v` database in the working directory
    db_files = [f for f in os.listdir() if f.startswith("panelapp_v") and f.endswith(".db")]
    if not db_files:
        raise FileNotFoundError("No `panelapp_v` database found in the working directory.")
    
    # Sort to get the latest file
    db_files.sort(reverse=True)
    latest_file = db_files[0]
    
    # Extract the version date from the filename
    version_date = latest_file.split("panelapp_v")[1].split(".")[0]
    panel_retrieved_date = f"{version_date[:4]}-{version_date[4:6]}-{version_date[6:]}"

    # Default clinical IDs if none provided
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

    if patient_data:
        logging.info("Using user-provided patient data.")
        for record in patient_data:
            patient_id = record.get("patient_id", f"Patient_{random.randint(10000000, 99999999)}")
            clinical_id = record.get("clinical_id", random.choice(clinical_ids))
            test_date = record.get("test_date", default_test_date)
            
            patients.append({
                "patient_id": patient_id,
                "clinical_id": clinical_id,
                "test_date": test_date,
                "panel_retrieved_date": panel_retrieved_date,
            })
    else:
        logging.info("Generating random patient data.")
        for _ in range(num_patients):
            patient_id = f"Patient_{random.randint(10000000, 99999999)}"
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


def save_to_database(df, database_name="patient_database.db", table_name="patient_data"):
    """
    Save the DataFrame to an SQLite database.

    Args:
        df (pd.DataFrame): DataFrame to save.
        database_name (str): SQLite database file name.
        table_name (str): Name of the table to store the data.
    """
    try:
        conn = sqlite3.connect(database_name)
        logging.info(f"Connected to database '{database_name}'.")
        
        # Append the data to the table
        df.to_sql(table_name, conn, if_exists="append", index=False)
        
        logging.info(f"Data successfully added to table '{table_name}' in '{database_name}'.")
        conn.close()
        logging.info("Database connection closed.")
    except Exception as e:
        logging.error(f"An error occurred while saving to the database: {e}")
        raise

def parse_arguments():
    """
    Parse command-line arguments for generating the patient database.
    """
    parser = argparse.ArgumentParser(description="Generate a patient database with optional user input.")
    
    parser.add_argument(
        "--num_patients", 
        type=int, 
        default=500, 
        help="Number of patient records to generate if no input data is provided."
    )
    parser.add_argument(
        "--clinical_ids", 
        type=str, 
        nargs="+", 
        help="List of clinical IDs to use. Example: R169 R419 R56"
    )
    parser.add_argument(
        "--default_test_date", 
        type=str, 
        help="Default test date in 'YYYY-MM-DD' format if not provided in patient_data."
    )
    parser.add_argument(
        "--patient_data", 
        type=str, 
        help="Path to a JSON file containing user-defined patient data. Each record should include 'patient_id', 'clinical_id', and 'test_date'."
    )
    return parser.parse_args()


def main():
    """
    Main function to generate and store the patient database based on user input or defaults.
    """
    setup_logging()
    logging.info("Script started.")

    args = parse_arguments()

    # Load patient data from JSON if provided
    patient_data = None
    if args.patient_data:
        try:
            with open(args.patient_data, "r") as f:
                patient_data = json.load(f)
            logging.info(f"Loaded patient data from {args.patient_data}.")
        except Exception as e:
            logging.error(f"Failed to load patient data from {args.patient_data}: {e}")
            return

    # Generate the patient database
    patient_df = generate_patient_database(
        num_patients=args.num_patients,
        patient_data=patient_data,
        clinical_ids=args.clinical_ids,
        default_test_date=args.default_test_date,
    )

    # Save to SQLite database
    save_to_database(patient_df)

    logging.info("Script completed successfully.")


if __name__ == "__main__":
    main()
