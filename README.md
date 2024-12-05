
# PanelGeneMapper

**PanelGeneMapper** is a tool designed to integrate PanelApp data with patient laboratory systems, providing a seamless workflow to update, retrieve, and manage gene panel information.

---

## **Installation**

### Prerequisites
1. Python version `>=3.9`
2. `pip` and `setuptools` installed.
3. Ensure your environment supports `cron` for scheduled updates (Linux/Mac) or a task scheduler for Windows.

### Steps
1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/YourRepo/PanelGeneMapper.git
   cd PanelGeneMapper
   ```

2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

---

## **Usage**

### 1. **Step 1: Build PanelApp Database**
   Run the `build_panelApp_database` module to fetch and process the PanelApp data:
   ```bash
   python -m PanelGeneMapper.build_panelApp_database
   ```
   This script will:
   - Fetch the latest gene panels from PanelApp.
   - Process the data into a structured format.
   - Save the data into an SQLite database (`panelapp_v*.db`).

---

### 2. **Step 2: Integrate Patient Data**
   Use the `build_patient_database` module to create a patient database and integrate with the PanelApp database:
   ```bash
   python -m PanelGeneMapper.build_patient_database --num_patients 1000
   ```
   Options:
   - `--num_patients`: Number of random patients to generate (default: 500).
   - `--patient_data`: Provide a JSON file with patient data.
   - `--default_test_date`: Default test date (e.g., `YYYY-MM-DD`).

---

### 3. **Step 3: Retrieve Data**
   Use the `retrieve_data` module to:
   - Add patients.
   - Retrieve gene lists.
   - List patients.

#### Example: Retrieve Gene List
```bash
python -m PanelGeneMapper.retrieve_data retrieve_genes --r_code R169 --output_file gene_list.csv
```
Other commands:
- `update`: Update the PanelApp database.
- `list_patients`: List all patients in the database.
- `add_patient`: Add a new patient.

---

### 4. **Step 4: Configure Settings**
   Use the `settings.py` module to schedule updates or run them manually.

#### Example: Schedule Updates
```bash
python -m PanelGeneMapper.settings interval daily
```
Options for interval:
- `5min`, `daily`, `weekly`, `monthly`, `6months`, `yearly`.

---

## **Folder Structure**
- `PanelGeneMapper/`
  - `build_panelApp_database.py`: Fetch and process PanelApp data.
  - `build_patient_database.py`: Create and manage patient databases.
  - `retrieve_data.py`: Main script for retrieving data.
  - `settings.py`: Configure and manage update settings.
- `config/`: Contains configuration files.

---

## **Logs and Outputs**
- Logs are saved in the root directory (e.g., `retrieve_data.log`, `build_panelApp_db_info_log.log`).
- Outputs like CSV files are saved to the specified path during execution.

---

## **Common Issues**
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

Feel free to reach out for support or create an issue in the repository for further assistance.
