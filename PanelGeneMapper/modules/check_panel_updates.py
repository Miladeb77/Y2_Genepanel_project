import os
import logging
import requests
import pandas as pd
import sqlite3


def get_panel_app_list():
    """
    Queries the Panel App API to return details on all signed-off Panels.

    Returns:
        pd.DataFrame: DataFrame containing panel_id and version from the API.
    """
    server = "https://panelapp.genomicsengland.co.uk"
    ext = "/api/v1/panels/"
    headers = {"Content-Type": "application/json"}

    # Initial API call
    response = requests.get(server + ext, headers=headers)

    # Handle API errors
    if not response.ok:
        response.raise_for_status()

    # Normalize the first page of results
    panel_app_df = pd.json_normalize(response.json(), record_path=["results"])
    all_dataframes = [panel_app_df]

    # Fetch subsequent pages
    while response.json().get("next") is not None:
        response = requests.get(response.json()["next"], headers=headers)
        next_page_df = pd.json_normalize(response.json(), record_path=["results"])
        all_dataframes.append(next_page_df)

    # Combine all pages into a single DataFrame
    panel_app_df = pd.concat(all_dataframes, ignore_index=True)

    # Return only id and version columns, renamed for clarity
    return panel_app_df[["id", "version"]].rename(columns={"id": "panel_id"})


def compare_panel_versions():
    """
    Compare panel versions between the latest local database in the databases folder and the PanelApp API.

    Returns:
        None
    """
    try:
        # Define the databases directory
        script_dir = os.path.abspath(os.path.dirname(__file__))
        project_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
        databases_dir = os.path.join(project_dir, "databases")

        # Find the latest PanelApp database
        db_files = [
            f for f in os.listdir(databases_dir)
            if f.startswith("panelapp_v") and f.endswith(".db")
        ]
        if not db_files:
            logging.error("No `panelapp_v` database found in the databases directory.")
            return

        # Sort databases by version and select the latest
        db_files.sort(reverse=True)
        latest_db = db_files[0]
        db_path = os.path.join(databases_dir, latest_db)

        logging.info(f"Using latest local PanelApp database: {latest_db}")

        # Connect to the local database
        with sqlite3.connect(db_path) as conn:
            local_df = pd.read_sql_query("SELECT panel_id, version FROM panel_info", conn)

        logging.info("Retrieved panel data from the local database.")

        # Fetch panel data from the API
        api_df = get_panel_app_list()
        logging.info("Retrieved panel data from the API.")

        # Compare the local database and API versions
        merged_df = pd.merge(
            local_df,
            api_df,
            on="panel_id",
            how="outer",
            suffixes=("_local", "_api"),
            indicator=True,
        )

        # Find and log differences
        differences = merged_df[merged_df["_merge"] != "both"]
        if not differences.empty:
            logging.warning("Differences found between local and API versions:")
            logging.warning(differences)
        else:
            logging.info("No differences found. Local database matches the API.")

    except Exception as e:
        logging.error(f"An error occurred during comparison: {e}")


if __name__ == "__main__":
    # Configure logging
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logs_dir = os.path.join(project_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "panelapp_comparison.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

    logging.info("Starting PanelApp version comparison...")
    compare_panel_versions()
