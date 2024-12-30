# User Guide for PanelGeneMapper CLI Tool

## Overview
**PanelGeneMapper**
- Command-line interface (CLI) tool designed to integrate PanelApp data with laboratory systems. The tool enables users to:
    - Search for patients and retrieve a list of R codes that have been tested on the patient.
    - Search for a specific R code and view the list of genes associated with that panel.
    - Timestamp when R codes were tested on patients, allowing users to compare the genes in a panel at the time of testing with the current version of the panel to identify any differences.
    - Retrieve a BED file for genes in a specific panel, facilitating genomic data analysis.

This guide provides instructions on how to interact with the available commands to achieve the desired results.



### 1. Update Local PanelApp Database 

python main.py update
Description: Updates the local PanelApp database with the latest data from the PanelApp API. This ensures that your local copy of the database is synchronized with the most recent available information.


### 2. List All Patients in the Database

python main.py list_patients --patient_db <path_to_patient_db> --save
Description: Lists all patients in the database. Optionally, you can save the list to a CSV file.

Options: 
--patient_db: (Optional) Path to the patient database. Defaults to patient_database.db if not specified.
--save: (Optional) If provided, saves the list of patients to a CSV file.

Example:

python main.py list_patients --patient_db ./databases/patient_database.db --save


### 3. Add a New Patient to the Database

python main.py add_patient --patient_db <path_to_patient_db> --patient_id <patient_id> --clinical_id <clinical_id> --test_date <test_date>

Description: Adds a new patient to the database with specified details.

Options:
--patient_db: (Optional) Path to the patient database. Defaults to patient_database.db.
--patient_id: (Required) The unique ID for the patient.
--clinical_id: (Required) The clinical ID associated with the patient.
--test_date: (Required) The test date in the format YYYY-MM-DD.

Example:

python main.py add_patient --patient_id 1234 --clinical_id 5678 --test_date 2024-12-30



### 4. Retrieve Gene List for Specific Patients

python main.py retrieve_genes --patient_db <path_to_patient_db> --panelapp_db <path_to_panelapp_db> --output_file <output_file> --r_code <r_code> --patient_id <patient_id> --archive_folder <archive_folder>

Description: Retrieves a gene list for a specific patient or clinical ID.

Options:
--patient_db: (Optional) Path to the patient database. Defaults to patient_database.db.
--panelapp_db: (Optional) Path to the PanelApp database.
--output_file: (Optional) The path to save the resulting CSV file. Defaults to output/gene_list.csv.
--r_code: (Optional) Filter by specific clinical ID.
--patient_id: (Optional) Filter by specific patient ID.
--archive_folder: (Optional) The name of the folder containing archived databases.

Example:

python main.py retrieve_genes --patient_db ./databases/patient_database.db --panelapp_db ./databases/panelapp_v20241230.db --output_file ./output/gene_list.csv --r_code 5678



### 5. Compare Local Database with the Latest API Data
python main.py compare_with_api

Description: Compares the local PanelApp database with the latest version from the PanelApp API to identify discrepancies or updates.

Example:
python main.py compare_with_api


### 6. Generate a BED File from Gene List
python main.py generate_bed --csv_file <path_to_csv> --r_code <r_code> --patient_id <patient_id> --output_file <output_file>

Description: Generates a BED file from the gene list provided or from the patient database.

Options:
--csv_file: (Optional) Path to a CSV file containing Ensembl gene IDs. If not provided, the tool uses data from the patient database.
--r_code: (Optional) Filter by specific clinical ID.
--patient_id: (Optional) Filter by specific patient ID.
--output_file: (Optional) Path to save the resulting BED file. Defaults to ../output/gene_exons.bed.

Example:
python main.py generate_bed --csv_file ./output/gene_list.csv --output_file ./output/gene_exons.bed


### Error Handling
If an error occurs during command execution, it will be logged, and common errors include:

Invalid file paths: Ensure that the paths for databases or output files are correct.
Missing arguments: Some commands require specific arguments, such as --patient_id or --test_date.
Internal errors: Issues related to database connections or file access may result in errors.
Log Files
The application generates logs for each operation, saved in the logs directory. Two log files are created:

panel_gene_mapper_info.log: Contains informational logs.
panel_gene_mapper_error.log: Contains error logs, which are useful for troubleshooting issues.
For detailed information on any issues, refer to the panel_gene_mapper_error.log.