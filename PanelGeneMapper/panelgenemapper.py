import argparse
import os
from modules.logging_utils import setup_logging
from modules.build_patient_database import save_to_database
from modules.build_panelApp_database import update_database
from modules.database_utils import retrieve_latest_panelapp_db, connect_and_join_databases
from modules.panelapp_api import get_panel_app_list

def parse_arguments():
    """
    Parse command-line arguments for the script.
    """
    parser = argparse.ArgumentParser(
        description="PanelGeneMapper: A Tool for Integrating PanelApp Data with Lab Systems and Generating BED Files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands.")

    # Subparser for updating the PanelApp database
    subparsers.add_parser("update", help="Update the local PanelApp database.")

    # Subparser for listing patients
    list_parser = subparsers.add_parser("list_patients", help="List all patients in the database.")
    list_parser.add_argument("--patient_db", required=True, help="Path to the patient database.")

    # Subparser for adding a patient
    add_patient_parser = subparsers.add_parser("add_patient", help="Add a new patient to the database.")
    add_patient_parser.add_argument("--patient_db", required=True, help="Path to the patient database.")
    add_patient_parser.add_argument("--patient_id", required=True, help="Patient ID to add.")
    add_patient_parser.add_argument("--clinical_id", required=True, help="Clinical ID for the patient.")
    add_patient_parser.add_argument("--test_date", required=True, help="Test date in YYYY-MM-DD format.")

    # Subparser for retrieving genes
    retrieve_genes_parser = subparsers.add_parser(
        "retrieve_genes", help="Retrieve gene lists for specific R codes or patient IDs."
    )
    retrieve_genes_parser.add_argument("--patient_db", required=True, help="Path to the patient database.")
    retrieve_genes_parser.add_argument("--panelapp_db", help="Path to the PanelApp database.")
    retrieve_genes_parser.add_argument("--output_file", required=True, help="Path to save the resulting CSV.")
    retrieve_genes_parser.add_argument("--r_code", help="Filter by specific R code (clinical_id).")
    retrieve_genes_parser.add_argument("--patient_id", help="Filter by specific patient ID.")
    retrieve_genes_parser.add_argument("--archive_folder", default="archive_databases", help="Path to archive folder.")

    return parser.parse_args()

def main():
    """
    Main entry point for the script.
    """
    setup_logging()
    args = parse_arguments()

    if args.command == "update":
        # Update the PanelApp database
        update_database()

    elif args.command == "list_patients":
        # List all patients in the database
        from modules.database_utils import list_patients
        list_patients(args.patient_db)

    elif args.command == "add_patient":
        # Add a new patient to the database
        from modules.build_patient_database import save_to_database
        save_to_database(args.patient_db, args.patient_id, args.clinical_id, args.test_date)

    elif args.command == "retrieve_genes":
        # Retrieve and process gene lists
        panelapp_db, is_temp = retrieve_latest_panelapp_db(args.archive_folder, args.panelapp_db)
        connect_and_join_databases(
            patient_db=args.patient_db,
            panelapp_db=panelapp_db,
            output_file=args.output_file,
            r_code=args.r_code,
            patient_id=args.patient_id,
            archive_folder=args.archive_folder
        )
        if is_temp:
            os.remove(panelapp_db)

if __name__ == "__main__":
    main()
