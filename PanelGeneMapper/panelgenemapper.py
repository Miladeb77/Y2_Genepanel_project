import argparse
import os
import logging
from modules.custom_logging import setup_logging
from modules.build_panelApp_database import main as update_database
from modules.patient_db_lookup_add import add_patient, list_patients, get_databases_dir
from modules.retrieve_gene_local_db import connect_and_join_databases, retrieve_latest_panelapp_db
from modules.check_panel_updates import compare_panel_versions
from modules.make_bed_file import create_local_db, extract_ensembl_ids_from_csv, extract_ensembl_ids_with_join, write_bed_file, fetch_all_data

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
    list_parser.add_argument("--patient_db", default=default_patient_db, help="Please provide patient database path if not default directory. The default is <..,..,databases\patient_database>")
    list_parser.add_argument("--save", action="store_true", help="Save the patient list to a CSV file.")


    # Subparser for adding a patient
    add_patient_parser = subparsers.add_parser("add_patient", help="Add a new patient to the database.")
    add_patient_parser.add_argument("--patient_db", default=default_patient_db, help="Please provide patient database path if not default directory. The default is <..,..,databases\patient_database>")
    add_patient_parser.add_argument("--patient_id", required=True, help="Patient ID to add.")
    add_patient_parser.add_argument("--clinical_id", required=True, help="Clinical ID associated with the patient.")
    add_patient_parser.add_argument("--test_date", required=True, help="Test date in 'YYYY-MM-DD' format.")

    # Subparser for retrieving gene lists
    retrieve_genes_parser = subparsers.add_parser(
        "retrieve_genes", help="Retrieve gene lists for specific R codes or patient IDs."
    )
    retrieve_genes_parser.add_argument("--patient_db", default=default_patient_db, help="Please provide patient database path if not default directory. The default is <..,..,databases\patient_database>")
    retrieve_genes_parser.add_argument("--panelapp_db", help="Please provide panelapp database path if not default directory. The default is <..,..,databases\panelapp_v..year..month..day..>")
    retrieve_genes_parser.add_argument("--output_file", default="output/gene_list.csv", help="Path to save the resulting table.")
    retrieve_genes_parser.add_argument("--r_code", help="Filter by specific R code (clinical_id).")
    retrieve_genes_parser.add_argument("--patient_id", help="Filter by specific patient ID.")
    retrieve_genes_parser.add_argument("--archive_folder", default=default_archive_folder, help="Name of the archive folder.")

    # Subparser for comparing local database with API
    compare_parser = subparsers.add_parser(
        "compare_with_api", help="Compare the local PanelApp database with the latest API data."
    )
    generate_bed_parser = subparsers.add_parser(
        "generate_bed", help="Generate BED file from Ensembl IDs."
        )
    generate_bed_parser.add_argument(
    "--csv_file",
    type=str,
    help=r"Ensure to specify the full path to the CSV file, e.g., C:\Users\nourm\Project\group_project\github_release\Y2_Genepanel_project\output\gene_list_patient_id_Patient_90184161.csv",)

    generate_bed_parser.add_argument("--r_code", help="Filter by specific R code (clinical_id).")
    generate_bed_parser.add_argument("--patient_id", help="Filter by specific patient ID.")
    generate_bed_parser.add_argument(
    "--output_file",
    type=str,
    default=os.path.join("..", "output", "gene_exons.bed"),
    help="Path to save the BED file.",)

    return parser.parse_args()

def generate_bed(args):
    """
    Generate a BED file based on Ensembl gene IDs retrieved from the patient database.
    """
    logging.info(f"Generating BED file for patient database")

    output_file = os.path.join("..", "output", "gene_exons.bed")
    
    # Define species and API details
    species = "homo_sapiens"
    server = "https://rest.ensembl.org"
    headers = {"Content-Type": "application/json"}
    
    create_local_db()
    
    # Extract Ensembl IDs
    if args.csv_file:
        # Extract from CSV if provided
        ensembl_gene_ids = extract_ensembl_ids_from_csv(args.csv_file)
    else:
        # Extract using database
        ensembl_gene_ids = extract_ensembl_ids_with_join(
            patient_db=os.path.join("..", "databases", "patient_database.db"),
            r_code=args.r_code,
            patient_id=args.patient_id,
        )
    data_list = fetch_all_data(ensembl_gene_ids, species, server, headers)
    
    write_bed_file(data_list, output_file)
    
    logging.info(f"BED file generated and saved to {args.output_file}")
    

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
            
        elif args.command == "generate_bed":
            generate_bed(args)
        else:
            logging.error("Invalid command. Use --help to see available commands.")

    except Exception as e:
        logging.error(f"An error occurred while executing the command: {e}")


if __name__ == "__main__":
    main()
