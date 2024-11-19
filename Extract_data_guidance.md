# Setup and Testing Guide for panelApp_extract_data.py

### Prerequisites

  -	Ensure Anaconda or Miniconda is installed on your machine.


### Step 1: Set Up the Conda Environment

1.	Create the environment:

Use the environment.yml file to set up the environment:

    conda env create -f environment.yml
    
2.	Activate the environment:

         conda activate PanelApp_project

3.	Select the environment in VS code (if using VS code):

	-	First close and re-open your VS code so that it can recognize the PanelApp_project conda environment (if you were originally connected to your remote VM using SSH on VS code, don't forget to set up the connection again)
    -	Open VS code.
	-	Press Ctrl+Shift+P (or Cmd+Shift+P on Mac) to open the command palette.
	-	Type and select Python: Select Interpreter 
	-	Choose the PanelApp_project environment from the list

This ensures that VS code uses the PanelApp_project conda environment for running and debugging your code.

4.	Install additional dependencies (if any) listed in requirements.txt:

        pip install -r requirements.txt
  	

### Step 2: Configure Environment Settings

1.	Disable automatic activation of the base environment:

        conda config --set auto_activate_base false

	-	This prevents Conda from automatically activating the base environment each time you open a new shell or source .bashrc.
	-	After running this command, reload the shell configuration to apply the changes:

        	source ~/.bashrc


2.	Set Nano as the default editor:

        echo 'export EDITOR=nano' >> ~/.bashrc

	-	This makes Nano the default editor, which is useful for editing files and crontab.

3.	Reload the configuration:

        source ~/.bashrc

### Step 3: Prepare for Cron Job Setup

1.	Locate the Python interpreter path:

        which python

	-	Note down the output, as you’ll need it for the cron job setup.

2.	Open the crontab editor:

        crontab -e

	-	The editor should open in Nano since we set it as the default editor.

### Step 4: Configure Cron Job for Automated Database Generation

1.	Add the following cron job to run the script every five minutes (for testing purposes):

        */5 * * * * <path_to_python> <path_to_script>/panelApp_extract_data.py

	-	Replace <path_to_python> with the path from which python.
	-	Replace <path_to_script> with the full path to panelApp_extract_data.py.

2.	Save and exit the crontab editor:
 
	-	Press Ctrl+X, then Y, then Enter to save.

3.	Verify cron job execution:
 
	Wait approximately 25 minutes, then check:
	-	The archive_databases folder contains compressed previous database versions.
	-	The latest database is in the main working directory.
	-	The info_log.log and error_log.log files contain logs from each program execution. info_log.log includes informational messages, while error_log.log logs errors encountered during script execution. 

### Step 5: Finalize Cron Job for Monthly Execution

1.	Remove test output files:

After confirming the cron job works as expected every five minutes, delete test outputs to start fresh:

-	Remove the archive_databases folder.
-	Delete the latest database file from your working directory.
-	Delete info_log.log and error_log.log
 
2.	Edit the crontab for monthly execution:

	-	Open the crontab editor:

        	crontab -e


	-	Change the cron job timing from */5 * * * * to 0 0 1 * * to schedule the script for monthly execution at midnight on the first day of each month:

        	0 0 1 * * <path_to_python> <path_to_script>/panelApp_extract_data.py


	-	Save and exit the editor as before (Ctrl+X, Y, then Enter).


### Step 6: Disable the Cron Job (if needed)

-	To stop the cron job without deleting it, open the crontab editor:

    	crontab -e


-	Add a # at the beginning of the cron job line to comment it out:

    	# 0 0 1 * * <path_to_python> <path_to_script>/panelApp_extract_data.py


-	Save and exit.
