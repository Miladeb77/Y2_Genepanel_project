
# PanelGeneMapper

**PanelGeneMapper** is a tool designed to integrate PanelApp data with patient laboratory systems, providing a seamless workflow to update, retrieve, and manage gene panel information.

---

## Installation

### Prerequisites
1. Python version `>=3.9`
2. `pip` and `setuptools` installed.

### Steps
1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/Miladeb77/Y2_Genepanel_project.git
   cd Y2_Genepanel_project
   ```
   
2. Create and activate conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate PanelApp_project
   ```

3. Install the dependencies using the provided `environment.yml` file:
   ```bash
   pip install .
   ```
4. Navigate to the PanelGeneMapper directory
   ```bash
   cd PanelGeneMapper
   ```

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

optional arguments:
  -h, --help            Use this to view commands

#### Example: Retrieve Gene List

```bash
python panelgenemapper.py retrieve_genes --help
```
```bash
python panelgenemapper.py retrieve_genes --r_code R169 --output_file gene_list.csv
```
```bash
python panelgenemapper.py retrieve_genes --patient_id Patient_85969552
```
```bash
python panelgenemapper.py retrieve_genes --r_code R420 --patient_id Patient_85969552
```

#### Example: Generate a Bed File

```bash
python panelgenemapper.py generate_bed --help
```

```bash
python panelgenemapper.py generate_bed --csv_file Y2_Genepanel_project/output/gene_list.csv
```
```bash
python panelgenemapper.py generate_bed --r_code R420
```
```bash
python panelgenemapper.py generate_bed --patient_id Patient_85969552
```
```bash
python panelgenemapper.py generate_bed --r_code R420 --patient_id Patient_85969552
```

#### Example: Add new patients to the database 

```bash
python panelgenemapper.py add_patient --help
```

```bash
python panelgenemapper.py add_patient --patient_id Patient_1234  --clinical_id R169 --test_date 2023-11-11
```


### 5. Check For Updates
Check for updates on panelapp
```bash
python panelgenemapper.py compare_with_api
```

### 6. Run Updates
Check for updates periodically using the `panelgenemapper.py` script:
```bash
python panelgenemapper.py update
```

---

## Project Structure

```
Y2_Genepanel_project/
├── PanelGeneMapper/
    ├── modules/
       ├── __init__.py                # Makes the folder a Python package
       ├── build_patient_database.py  # Functions for handling patient database
       ├── build_panelApp_database.py # Functions for handling PanelApp database
       ├── database_utils.py          # Shared database-related utilities
       ├── logging_utils.py           # Logging setup and utilities
       ├── panelapp_api.py            # Functions for interacting with the PanelApp API
    ├── __init__.py
    ├── panelgenemapper.py             # Main script (contains argparse and main function)
├── configuration/
    ├── build_panelApp_database_config.json
├── databases/
    ├── panelapp_v20241223.db
    ├── patient_database.db
    ├── local_patient_database.json
├── archive_databases/
    ├── panelapp_v20241220.db.gz
├── tests/                        
    ├── __init__.py
    ├── test_api_ensembl.py
    ├── test_build_panelApp_database.py
    ├── test_build_patient_database.py
    ├── test_check_panel_updates.py
    ├── test_custom_logging
├── environment.yml                # Dependencies and environment configuration
├── requirement.txt
├── README.md                      # Documentation

```

### Description of Key Components
- **`modules/`**: Contains modularized Python files for specific tasks.
  - `build_patient_database.py`: Functions for managing patient databases, such as saving new records.
  - `build_panelApp_database.py`: Functions for managing PanelApp databases, including updates.
  - `database_utils.py`: Shared utility functions for database handling, such as retrieving or merging databases.
  - `logging_utils.py`: Setup and configuration for logging within the project.
  - `panelapp_api.py`: Functions to interact with the PanelApp API for data retrieval.
- **`panelgenemapper.py`**: The main entry point for the project. Handles command-line arguments, orchestrates various tasks, and integrates all modules.
- **`environment.yml`**: Specifies dependencies and environment setup for the project.
- **`README.md`**: Provides documentation for the project, including installation, usage, and structure.

---

## Logs and Outputs
- Logs are saved in the root directory (e.g., `panelgenemapper.log`, `build_panelApp_db_info.log`).
- Outputs such as CSV files are saved to the specified path during execution.

---

## Common Issues

1. **Python Encoding Errors**:
   Set the environment variable:
   ```bash
   export PYTHONIOENCODING=utf-8
   ```

2. **Database Not Found**:
   Ensure you have run `build_panelApp_database` before using patient data or retrieving genes.

3. **Permission Issues**:
   Run commands with appropriate permissions or in a writable directory.

---

## Contributing
Feel free to submit pull requests or create issues for bugs, features, or general feedback.
