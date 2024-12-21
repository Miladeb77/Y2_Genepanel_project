# App.py

app.py is a Flask-based web application that interfaces with a local SQLite database of patient data and PanelApp databases. It provides various endpoints for retrieving patient information, validating R-codes, and comparing stored data with live data from PanelApp.

## This application supports:

-	Fetching and displaying patient data.
 
-	Adding new patient records (validated by a list of valid R-codes).
 
-	Serving a simple frontend (e.g., index.html in static/).
 
-	Handling scenarios where user input is requested (e.g., for unknown R-codes).
 
-	Logging of all key events and errors for auditing and debugging.

## Important Setup Requirements

-	Place app.py in the root directory of your project.
The application is designed to run from the project’s root. If you move it into a subdirectory, some relative paths might break.

- Put all frontend files (e.g., index.html, script.js, style.css) in a folder called static/ in the root directory.
Flask uses app.static_folder to serve static content. This folder name should not be changed for the default setup.

-	Include a config/ directory in the root directory and place app_config.json inside it.
The file name must remain app_config.json, as app.py looks specifically for this name.

-	You may also place build_panelApp_database_config.json in the same config/ folder if your application needs it.
  
-	Use the provided naming convention and structure
This ensures that your environment, logs, and config files are all located where the application expects them.

## Project Structure

A sample folder layout reflecting these requirements:

    Y2_Genepanel_project/
    ├── config/
    │   ├── app_config.json
    │   └── build_panelApp_database_config.json
    ├── logs/
    │   └── Flask_app_logs/
    │       ├── info_log.log
    │       └── error_log.log
    ├── static/
    │   ├── index.html
    │   ├── script.js
    │   └── style.css
    ├── app.py
    ├── environment.yml
    └── requirements.txt

-	app.py: Main Flask application (must be at the root).
  
-	config/app_config.json: Primary config file for the Flask app.
  
-	config/build_panelApp_database_config.json: Contains additional PanelApp API settings (server URL, headers, etc.).
  
-	logs/Flask_app_logs/: Stores info_log.log and error_log.log.
  
-	static/: Contains your front-end files (index.html, script.js, style.css).
  
-	environment.yml and requirements.txt: Define Python dependencies.

## Features

### Patient Record Management

- GET /patient: Retrieve patient data by patient_id.
 
-	POST /patient/add: Create new patient records with a valid R-code.
  
### R-code-based Queries

- GET /rcode: Fetch records based on a specific R-code.
  
-	POST /rcode/handle: Handle user responses for previously unrecognized R-codes, optionally creating new patient records.
  
### PanelApp Data Integration

-   Most Recent Panel: Automatically detects the most recent PanelApp .db file.

-   Older Databases: Falls back to older databases if the R-code isn’t found in the latest one.

-   Live PanelApp Comparison: POST /compare-live-panelapp compares stored HGNC IDs with live data from PanelApp’s API.

### Static File Serving

-  GET /: Serves the index.html file from the static/ directory.

-  GET /<path:filename>: Serves any static file from static/.

### Robust Logging

- Logs are stored in ./logs/Flask_app_logs/.
  
-  info_log.log captures INFO and above.
  
-  error_log.log captures ERROR and above.
  
-  Console output also shows INFO and above for real-time monitoring.

## Configuration

### Logging

-  Handled by the function setup_logging() in app.py.
  
-  Creates or reuses ./logs/Flask_app_logs/info_log.log and ./logs/Flask_app_logs/error_log.log.
 
-  just logging behavior (levels, formats) inside setup_logging() if needed.
  
### Database Paths

-  Defined in ./config/app_config.json.
  
-  Make sure patient_db_path points to a valid SQLite file with a patient_data table.
  
-  Panel_dir must contain your PanelApp .db files (named like panelapp_vYYYYMMDD.db).

### Valid R-codes File

-  The file at r_code_file in app_config.json contains one R-code per line.
  
-  This list is used by /patient/add and /rcode to validate user-provided R-codes.
  
### PanelApp API Config

-  Located in config/build_panelApp_database_config.json.
  
-  Typically has:

        {
          "server": "https://api.panelapp.genomicsengland.co.uk",
          "headers": {
            "Accept": "application/json"
            // Possibly other headers like Authorization if needed
          }
        }


## Testing Endpoints

With the Flask app running (by default on http://127.0.0.1:5000 or http://localhost:5000):

### Open the main page:

-  In a browser: http://localhost:5000/
 
### Fetch patient data:

-  GET /patient?patient_id=Patient_123

### Add a new patient:

-  POST /patient/add with JSON body:

        {
          "patient_id": "Patient_123",
          "r_code": "R46"
        }


### Fetch by R-code:

-  GET /rcode?r_code=R46

### Handle unknown R-code:

-  POST /rcode/handle with JSON body like:

        {
          "response": "Yes",
          "r_code": "R46",
          "patient_ids": ["Patient_789"]
        }


### Compare with live PanelApp:

-  POST /compare-live-panelapp with JSON body:

        {
          "clinical_id": "R46",
          "existing_hgnc_ids": ["HGNC:12345", "HGNC:67890"]
        }



## Use a tool like Postman or curl to test these endpoints.

### Example curl Calls

-  Fetch patient

        curl "http://localhost:5000/patient?patient_id=Patient_123"

### Add patient

    curl -X POST -H "Content-Type: application/json" \
         -d '{"patient_id": "Patient_999", "r_code": "R46"}' \
         http://localhost:5000/patient/add



# generate_valid_rcode_list.py

The generate_valid_rcode_list.py script automates the process of discovering, extracting, and maintaining a list of valid “R-codes” (or disorders) from a PanelApp database. These valid R-codes are stored in an output file for use by other systems (e.g., a web application) to verify whether a submitted R-code is valid.

## By default, this script:
-	Locates a PanelApp database within the project directory.

-	Sets up comprehensive logging (to both a log file and the console).
  
-	Checks if there is a newly updated PanelApp .db file.
  
-	Extracts unique relevant disorders (R-codes) from this database.
  
-	Appends new (not-yet-seen) R-codes to an output file.
  
-	Repeats the process continuously in a loop, waiting 120 seconds between each run (for testing purposes).

## Project Structure

A typical directory layout could look like this:
	
	Y2_Genepanel_project/
	├─ logs/
	│   └─ generate_valid_rcode_list.log
	├─ generate_valid_rcodes_output/
	│   └─ unique_relevant_disorders.txt
	└─ PanelGeneMapper/
	    └─ generate_valid_rcode_list.py

-	logs/: Contains log files generated by this script (by default, generate_valid_rcode_list.log).
  
-	generate_valid_rcodes_output/: Stores the output file of valid R-codes (unique_relevant_disorders.txt).
  
-	PanelGeneMapper/: A folder where generate_valid_rcode_list.py might reside.

Note: The actual structure can vary; what matters is that you keep track of where the root directory is and where the PanelApp .db file is stored.

## Important Considerations

### 1. Locating the Root Directory

By default, the script determines the root directory like this:

	root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

This means:
-	The root directory is the parent folder of the folder where generate_valid_rcode_list.py resides.
  
-	If you move generate_valid_rcode_list.py to another location, or your project structure changes, you will need to update this line accordingly to ensure the script can correctly find its root directory.

### 2. Scheduled Execution and Sleep Interval

Inside the script, there is an infinite loop with a time.sleep(120) call, which waits 120 seconds (2 minutes) between each iteration of the script:

	while True:
   		main()
    		time.sleep(120)  # Wait for 2 minutes

This interval is primarily for testing or demonstration purposes (so you can see changes happen relatively quickly). In a real production scenario, you might want to run this less frequently—for example, once a month—to update the valid R-codes list. You can do this by:
-	Adjusting the time.sleep value (e.g., change to time.sleep(2592000) for 30 days).
  
-	Or disabling the infinite loop and scheduling the script via cron, systemd timers, or a CI/CD pipeline to run monthly.
 

By running this script regularly (e.g., monthly), you ensure your valid R-codes list always stays up-to-date with the latest medical or genetic information from PanelApp.

### Logging
-	File Logs: Everything from INFO level and above gets written to logs/generate_valid_rcode_list.log.
  
-	Console Logs: Warnings (WARNING level) and above are shown on the console.
  
-	You can tailor these levels in the setup_logging function.
