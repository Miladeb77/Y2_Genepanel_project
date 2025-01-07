# generate_valid_rcode_list.py

# Overview

The generate_valid_rcode_list.py script generates a list of valid R-codes from PanelApp databases and keeps this list up to date. This list is critical for validating R-codes when running the main web application (app.py). Before launching the web application, you must ensure this script has been run at least once so that a fresh list of valid R-codes is available.

This script is located inside the PanelGeneMapper directory in the root of the project:
	
	root_directory/
	└── PanelGeneMapper/
	    └── generate_valid_rcode_list.py

## What Does generate_valid_rcode_list.py Do?

-	Locate the PanelApp Database: It searches the project’s directories for a subdirectory containing at least one PanelApp SQLite database file (named panelapp_v*.db).

-	Check for New Database Versions: It determines whether there’s a new (unprocessed) version of the database by comparing the file name to a record of previously processed databases.

-	Extract Relevant Disorders: If a new database is found, the script connects to it and retrieves all unique values from the relevant_disorders field in the panel_info table.

-	Append Disorders to the Output File: These unique values (valid R-codes) are appended to an output text file (avoiding duplicates).

-	Logs Activities: The script writes logs for both general INFO messages and ERROR messages to separate log files.

## Why Is It Run Periodically?

The script is designed to run in an infinite loop so it can periodically check for new database versions that might appear. When a new version is detected, it automatically updates the list of valid R-codes.
	
-	By default, the script sleeps for 1 month (2678400 seconds) between each run.

-	If a new version of the database appears in the meantime, the script will process it in the next iteration.

## How to Change the Run Frequency

The frequency is controlled by the line (line 491) in generate_valid_rcode_list.py:

	time.sleep(2678400)  # Wait for 1 month before the next iteration

To change how often it runs, modify the integer value (in seconds):

-	For example, to run every day, change it to time.sleep(86400).

-	For every hour, time.sleep(3600).

## Requirements

PanelApp Database

You must have at least one valid PanelApp SQLite database file named panelapp_v*.db within the databases/ folder.

## How to Run the Program

Open a Terminal in the root of your project (where the PanelGeneMapper folder resides).

Execute the script:

	python PanelGeneMapper/generate_valid_rcode_list.py


Once the program starts, your current terminal will be blocked as long as the script is running. It continuously loops, only sleeping between runs.

-	If you want to continue working on other tasks in your command line, open a new terminal.

-	To stop the script, press CTRL + C in the terminal where it’s running. This will terminate the process.

## Logs and Output Files

### Log Files:
	
-	logs/generate_valid_rcode_list.log (records INFO-level and above messages)
 
-	logs/generate_valid_rcode_list_error.log (records ERROR-level messages)
 
### Output Directory: output/

-	The main output file for valid R-codes is unique_relevant_disorders.txt. Each new unique R-code is appended here (duplicates are skipped).



# app.py

# Overview

The app.py script is a Flask web application that provides endpoints for:

-	Managing patient records linked to specific R codes.

-	Retrieving gene panel information from PanelApp databases.

-	Comparing local data with live PanelApp data for consistency checks.

This application uses an SQLite database of patients (patient_database.db), alongside PanelApp database files, to serve requests from a frontend (HTML/JS) located in the static folder.

## What Does app.py Do?

-	Hosts a Flask App: Runs a local server (by default on http://localhost:5000/) that serves both a frontend (in the static folder) and a 	set of REST endpoints for data retrieval and creation.

-	Patient Record Management: Allows you to fetch patient data, add new patient records, and validate the R code (relevant disorder) against a known list of valid R codes.

-	PanelApp Database Interaction: Looks up gene panels associated with R codes by searching the PanelApp databases in a specified directory.

-	Live PanelApp Comparison: Offers an endpoint to compare locally stored HGNC IDs against the latest data from PanelApp’s API, identifying any new or removed genes.

## Where Do the Logs Go?

All logging messages from app.py are saved in a logs directory located at the project’s root. Specifically:

-	Flask_info_log.log: Stores all messages at INFO level and above.

-	Flask_error_log.log: Stores only messages at ERROR level and above.

Additionally, the application logs INFO-level messages to the console in real-time, so you can monitor the server output directly from your terminal.

## Requirements

Before running app.py, ensure you have:

### patient_database.db

-	This SQLite file must exist and contain the relevant schema (notably a patient_data table).

-	The path to this file will be specified in app_config.json (see below).

### PanelApp Databases

-	All versions of PanelApp database files referenced by any patient record in patient_database.db (via panel_retrieved_date field) must be present in the directory defined by panel_dir in app_config.json.

-	These files follow the naming pattern panelapp_vYYYYMMDD.db (or .db.gz if compressed).

### unique_relevant_disorders.txt

-	This file is generated by generate_valid_rcode_list.py.

-	It contains a list of valid R codes used for validating incoming R codes in the application.

-	The path to this file is set in app_config.json under "r_code_file".

## Configuration

### The app_config.json File

app.py loads critical paths and configuration details from a JSON file called app_config.json, located in the configuration/ folder at the root of the project. A typical structure looks like:

	{
	    "patient_db_path": "/absolute/path/to/patient_database.db",
	    "panel_dir": "/absolute/path/to/PanelGeneMapper",
	    "r_code_file": "/absolute/path/to/generate_valid_rcodes_output/unique_relevant_disorders.txt",
	    "build_panelApp_database_config.json": "/absolute/path/to/configuration/build_panelApp_database_config.json"
	}

-	patient_db_path: Absolute path to patient_database.db.

-	panel_dir: Directory containing PanelApp database files (panelapp_v*.db).

-	r_code_file: Path to the file with valid R codes (unique_relevant_disorders.txt).

-	build_panelApp_database_config.json: Path to an additional config file used for interacting with the live PanelApp API.

After editing app_config.json to match your environment, save the file. The application will read these paths at startup.

## How to Run the Web App

### Ensure Required Files Are in Place;

-	Confirm patient_database.db is at the location specified in app_config.json.

-	Confirm PanelApp databases are in the panel_dir subdirectory.

-	Confirm unique_relevant_disorders.txt is accessible at the path set in r_code_file.

### Move to the Project’s Root Directory

In your terminal:

	cd /path/to/project/root


### Run app.py

	python app.py

-	The Flask server will start on http://localhost:5000/ by default.

-	Your terminal will display INFO-level logs.

-	Access the web interface by opening http://localhost:5000/ in your browser.

## Front-End Files

The front-end (HTML/CSS/JS) for this Flask app is located in the static folder at the project root. When the server runs, it serves index.html (and other static assets) from this directory.
