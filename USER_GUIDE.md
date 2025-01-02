# User Guide for PanelGeneMapper CLI Tool

## Overview
**PanelGeneMapper**
- Command-line interface (CLI) tool designed to integrate PanelApp data with laboratory systems. The tool enables users to:
    - Search for patients and retrieve a list of R codes that have been tested on the patient.
    - Search for a specific R code and view the list of genes associated with that panel.
    - Timestamp when R codes were tested on patients, allowing users to compare the genes in a panel at the time of testing with the current version of the panel to identify any differences.
    - Retrieve a BED file for genes in a specific panel, facilitating genomic data analysis.

This guide provides instructions on how to interact with the available commands to achieve the desired results.

---

### 1. **Build PanelApp Database**

**Command:**
**`python -m modules.build_panelApp_database`**

**Description:**  
Fetches the latest gene panels from PanelApp, processes the data, and saves it into an SQLite database (e.g., panelapp_v*.db).

---

### 2. **Integrate Patient Data**

**Command:**  
**`python -m modules.build_patient_database --num_patients <number> --patient_data <path_to_patient_data> --default_test_date <test_date>`**

**Description:**  
Creates a patient database and integrates it with the PanelApp database.

**Options:**  
- **--num_patients:** (Optional) Number of random patients to generate (default: 500). 
- **--patient_data:** (Optional) Path to a JSON file containing patient data.
- **--default_test_date:** (Optional) Default test date (e.g., YYYY-MM-DD).
**Example:**  
**`python -m modules.build_patient_database --num_patients 1000 --default_test_date 2024-12-30`**

### 3. **List All Patients in the Database**

**Command:**  
**`python panelgenemapper.py list_patients <path_to_patient_db> --save`**

**Description:**  
Lists all patients in the database. Optionally, you can save the list to a CSV file.

**Options:**  
- **--patient_db:** (Optional) Path to the patient database. Defaults to `patient_database.db` if not specified.  
- **--save:** (Optional) If provided, saves the list of patients to a CSV file.

**Example:**  
**`python panelgenemapper.py list_patients --patient_db ./databases/patient_database.db --save`**

---

### 4. **Add a New Patient to the Database**

**Command:**  
**`python panelgenemapper.py add_patient --patient_id <patient_id> --clinical_id <clinical_id> --test_date <test_date>`**

**Description:**  
Adds a new patient to the database with specified details.

**Options:**  
- **--patient_db:** (Optional) Path to the patient database. Defaults to `patient_database.db`.  
- **--patient_id:** (Required) The unique ID for the patient.  
- **--clinical_id:** (Required) The clinical ID associated with the patient.  
- **--test_date:** (Required) The test date in the format YYYY-MM-DD.

**Example:**  
**`python main.py add_patient --patient_id 1234 --clinical_id 5678 --test_date 2024-12-30`**

---

### 5. **Retrieve Gene List for Specific Patients**

**Command:**  
**`python panelgenemapper.py retrieve_genes --r_code <r_code> --patient_id <patient_id> --output_file <output_file>`**

**Description:**  
Retrieves a gene list for a specific patient or clinical ID.

**Options:**  
- **--patient_db:** (Optional) Path to the patient database. Defaults to `patient_database.db`.  
- **--panelapp_db:** (Optional) Path to the PanelApp database.  
- **--output_file:** (Optional) The path to save the resulting CSV file. Defaults to `output/gene_list.csv`.  
- **--r_code:** (Optional) Filter by specific clinical ID.  
- **--patient_id:** (Optional) Filter by specific patient ID.  
- **--archive_folder:** (Optional) The name of the folder containing archived databases.

**Example:**  
**`python main.py retrieve_genes --patient_db ./databases/patient_database.db --panelapp_db ./databases/panelapp_v20241230.db --output_file ./output/gene_list.csv --r_code 5678`**

---

### 6. **Compare Local Database with the Latest API Data**

**Command:**  
**`python panelgenemapper.py compare_with_api`**

**Description:**  
Compares the local PanelApp database with the latest version from the PanelApp API to identify discrepancies or updates.

**Example:**  
**`python main.py compare_with_api`**

---

### 7. **Generate a BED File from Gene List**

**Command:**  
**`python panelgenemapper.py generate_bed --csv_file <path_to_csv> --r_code <r_code> --patient_id <patient_id> --output_file <output_fi`**

**Description:**  
Generates a BED file from the gene list provided or from the patient database.

**Options:**  
- **--csv_file:** (Optional) Path to a CSV file containing Ensembl gene IDs. If not provided, the tool uses data from the patient database.  
- **--r_code:** (Optional) Filter by specific clinical ID.  
- **--patient_id:** (Optional) Filter by specific patient ID.  
- **--output_file:** (Optional) Path to save the resulting BED file. Defaults to `../output/gene_exons.bed`.

**Example:**  
**`python main.py generate_bed --csv_file ./output/gene_list.csv --output_file ./output/gene_exons.bed`**

---

## Error Handling

If an error occurs during command execution, it will be logged. Common errors include:

- **Invalid file paths:** Ensure that the paths for databases or output files are correct.
- **Missing arguments:** Some commands require specific arguments, such as `--patient_id` or `--test_date`.
- **Internal errors:** Issues related to database connections or file access may result in errors.

### Log Files

The application generates logs for each operation, saved in the `logs` directory. Two log files are created:

- **panel_gene_mapper_info.log:** Contains informational logs.
- **panel_gene_mapper_error.log:** Contains error logs, useful for troubleshooting issues.

For detailed information on any issues, refer to the `panel_gene_mapper_error.log`.

---
