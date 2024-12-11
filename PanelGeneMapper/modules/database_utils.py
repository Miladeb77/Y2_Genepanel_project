import os
import sqlite3
import gzip
import shutil
import logging

def retrieve_latest_panelapp_db(archive_folder, panelapp_db):
    """
    Retrieve the latest PanelApp database from the working directory or archive folder.
    """
    try:
        if panelapp_db:
            return panelapp_db, False

        db_files = [f for f in os.listdir() if f.startswith("panelapp_v") and f.endswith(".db")]
        if db_files:
            db_files.sort(reverse=True)
            return db_files[0], False

        archived_files = [f for f in os.listdir(archive_folder) if f.startswith("panelapp_v") and f.endswith(".db.gz")]
        if archived_files:
            archived_files.sort(reverse=True)
            latest_archived = archived_files[0]

            temp_file = f"/tmp/{latest_archived.replace('.gz', '')}"
            with gzip.open(os.path.join(archive_folder, latest_archived), 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return temp_file, True

        raise FileNotFoundError("No PanelApp database found.")
    except Exception as e:
        logging.error(f"An error occurred while retrieving the PanelApp database: {e}")
        raise
