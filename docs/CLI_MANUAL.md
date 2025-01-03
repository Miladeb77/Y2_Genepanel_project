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

## Usage

### 1. Build PanelApp Database
Run the `build_panelApp_database` module to fetch and process the PanelApp data:
```bash
python -m modules.build_panelApp_database
```
This script will:
- Fetch the latest gene panels from PanelApp.
- Process the data into a structured format.
- Save the data into an SQLite database (`panelapp_v*.db`).

---

### 2. Integrate Patient Data
Use the `build_patient_database` module to create a patient database and integrate it with the PanelApp database:
```bash
python -m modules.build_patient_database --num_patients 1000
```
#### Integrate the local patient database by providing a JSON file. An example of json file can be found in the databases folder in the root directory.
```bash
python -m modules.build_patient_database --patient_data patient_data.json
```
Options:
- `--num_patients`: Number of random patients to generate (default: 500).
- `--patient_data`: Provide a JSON file with patient data.
- `--default_test_date`: Default test date (e.g., `YYYY-MM-DD`). 

---

---

### 3. Build the latest panelapp database
Use the `build_panelApp_database` module to create a patient database and integrate it with the PanelApp database:
```bash
python -m modules.build_panelApp_database
```
---

### 4. Retrieve Data
Use the `panelgenemapper.py` script to:
- Retrieve gene lists.
- Generate Bed Files.
- List patients in the database.
- Add patients
- Check for updates on PanelApp.
- Update the PanelApp local database.

### Available commands:
PanelGeneMapper: A Tool for Integrating PanelApp Data with Lab Systems and Generating BED Files.

positional arguments:
  {update,list_patients,add_patient,retrieve_genes,compare_with_api,generate_bed}

    update              Update the local PanelApp database.
    list_patients       List all patients in the database.
    add_patient         Add a new patient to the database.
    retrieve_genes      Retrieve gene lists for specific R codes or patient IDs.
    compare_with_api    Compare the local PanelApp database with the latest API data.
    generate_bed        Generate BED file from Ensembl IDs.
    
    -h, --help            Use this to view commands

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
- INFO-level logs and above are displayed in the console.

The logging configuration can be customized within the code, and the log files and logging levels can be adjusted by modifying the setup_logging() function.

For detailed information on any issues, refer to the `panel_gene_mapper_error.log`.

---
