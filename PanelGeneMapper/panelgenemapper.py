import argparse
import os
import logging
from modules.custom_logging import setup_logging
from modules.build_panelApp_database import main as update_database
from modules.patient_db_lookup_add import add_patient, list_patients, get_databases_dir
from modules.retrieve_gene_local_db import connect_and_join_databases, retrieve_latest_panelapp_db
from modules.check_panel_updates import compare_panel_versions


def configure_logging():
    """
    Configure centralized logging settings.
    """
    # Define the centralized logs directory
    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.abspath(os.path.join(script_dir, ".."))
    logs_dir = os.path.join(project_dir, "logs")

    # Set up logging
    setup_logging(
        logs_dir=logs_dir,
        info_log_file="panel_gene_mapper_info.log",
        error_log_file="panel_gene_mapper_error.log"
    )


def parse_arguments():
    """
    Parse command-line arguments for the script using subparsers.
    """
    parser = argparse.ArgumentParser(
        description="PanelGeneMapper: A Tool for Integrating PanelApp Data with Lab Systems and Generating BED Files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands.")

    # Define default paths dynamically
    databases_dir = get_databases_dir()
    default_patient_db = os.path.join(databases_dir, "patient_database.db")
    default_archive_folder = os.path.join(databases_dir, "archive_databases")

    # Subparser for updating the database
    update_parser = subparsers.add_parser("update", help="Update the local PanelApp database.")

    # Subparser for listing patients
    # Subparser for listing patients
    list_parser = subparsers.add_parser("list_patients", help="List all patients in the database.")
    list_parser.add_argument("--patient_db", default=default_patient_db, help="Path to the patient database.")
    list_parser.add_argument("--save", action="store_true", help="Save the patient list to a CSV file.")


    # Subparser for adding a patient
    add_patient_parser = subparsers.add_parser("add_patient", help="Add a new patient to the database.")
    add_patient_parser.add_argument("--patient_db", default=default_patient_db, help="Path to the patient database.")
    add_patient_parser.add_argument("--patient_id", required=True, help="Patient ID to add.")
    add_patient_parser.add_argument("--clinical_id", required=True, help="Clinical ID associated with the patient.")
    add_patient_parser.add_argument("--test_date", required=True, help="Test date in 'YYYY-MM-DD' format.")

    # Subparser for retrieving gene lists
    retrieve_genes_parser = subparsers.add_parser(
        "retrieve_genes", help="Retrieve gene lists for specific R codes or patient IDs."
    )
    retrieve_genes_parser.add_argument("--patient_db", default=default_patient_db, help="Path to the patient database.")
    retrieve_genes_parser.add_argument("--panelapp_db", help="Path to the PanelApp database.")
    retrieve_genes_parser.add_argument("--output_file", default="output/gene_list.csv", help="Path to save the resulting table.")
    retrieve_genes_parser.add_argument("--r_code", help="Filter by specific R code (clinical_id).")
    retrieve_genes_parser.add_argument("--patient_id", help="Filter by specific patient ID.")
    retrieve_genes_parser.add_argument("--archive_folder", default=default_archive_folder, help="Path to the archive folder.")

    # Subparser for comparing local database with API
    compare_parser = subparsers.add_parser(
        "compare_with_api", help="Compare the local PanelApp database with the latest API data."
    )

    return parser.parse_args()


def main():
    """
    Main function to parse arguments and execute the appropriate command.
    """
    configure_logging()
    args = parse_arguments()

    try:
        if args.command == "update":
            update_database()
            logging.info("Local PanelApp database updated successfully.")

        elif args.command == "list_patients":
            logging.info(f"Listing patients from database: {args.patient_db}")
            list_patients(args.patient_db, save_to_file=args.save)


        elif args.command == "add_patient":
            logging.info(f"Adding patient {args.patient_id} to database: {args.patient_db}")
            add_patient(args.patient_id, args.clinical_id, args.test_date)

        elif args.command == "retrieve_genes":
            logging.info(f"Retrieving genes for patient database: {args.patient_db}")
            panelapp_db_path, is_temp = retrieve_latest_panelapp_db(args.archive_folder, args.panelapp_db)
            connect_and_join_databases(
                patient_db=args.patient_db,
                panelapp_db=panelapp_db_path,
                output_file=args.output_file,
                r_code=args.r_code,
                patient_id=args.patient_id,
                archive_folder=args.archive_folder,
            )
            if is_temp:
                os.remove(panelapp_db_path)

        elif args.command == "compare_with_api":
            logging.info("Comparing local PanelApp database with API.")
            compare_panel_versions()

        else:
            logging.error("Invalid command. Use --help to see available commands.")

    except Exception as e:
        logging.error(f"An error occurred while executing the command: {e}")


if __name__ == "__main__":
    main()
