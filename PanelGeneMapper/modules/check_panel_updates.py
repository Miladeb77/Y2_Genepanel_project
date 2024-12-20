import requests
import logging
import pandas as pd
import sqlite3
import os


def get_panel_app_list():
    """
    Queries the Panel App API to return details on all signed-off Panels.

    Returns:
        pd.DataFrame: DataFrame containing panel_id and version from the API.
    """
    server = "https://panelapp.genomicsengland.co.uk"
    ext = "/api/v1/panels/"

    r = requests.get(server + ext, headers={"Content-Type": "application/json"})

    # Handle API errors
    if not r.ok:
        r.raise_for_status()

    # Create the initial DataFrame
    panel_app_df = pd.json_normalize(r.json(), record_path=["results"])

    # List to store all DataFrames
    all_dataframes = [panel_app_df]

    # Iterate over remaining pages
    while r.json().get("next") is not None:
        r = requests.get(r.json()["next"], headers={"Content-Type": "application/json"})
        next_page_df = pd.json_normalize(r.json(), record_path=["results"])
        all_dataframes.append(next_page_df)

    # Concatenate all DataFrames
    panel_app_df = pd.concat(all_dataframes, ignore_index=True)

    # Select only id and version columns
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

        # Find the latest PanelApp database in the databases directory
        db_files = [f for f in os.listdir(databases_dir) if f.startswith("panelapp_v") and f.endswith(".db")]
        if not db_files:
            logging.error(f"No `panelapp_v` database found in the databases directory: {databases_dir}")
            return

        # Sort and select the latest version
        db_files.sort(reverse=True)
        latest_db = db_files[0]
        db_path = os.path.join(databases_dir, latest_db)

        logging.info(f"Using latest local PanelApp database: {latest_db}")

        # Connect to the local database
        conn = sqlite3.connect(db_path)

        # Retrieve panel_id and version from the local database
        local_df = pd.read_sql_query("SELECT panel_id, version FROM panel_info", conn)
        conn.close()

        logging.info("Retrieved panel data from the local database.")

        # Call `get_panel_app_list` to fetch data from the API
        api_df = get_panel_app_list()

        logging.info("Retrieved panel data from the API.")

        # Compare the two DataFrames
        merged_df = pd.merge(
            local_df,
            api_df,
            on="panel_id",
            how="inner",
            suffixes=("_local", "_api"),
            indicator=True,
        )

        # Identify differences
        differences = merged_df[
            (merged_df["_merge"] != "both") | (merged_df["version_local"] != merged_df["version_api"])
        ]

        if not differences.empty:
            logging.warning("Differences found between local and API versions:")
            logging.warning(differences)
        else:
            logging.info("No differences found. Local database matches the API.")

    except Exception as e:
        logging.error(f"An error occurred during comparison: {e}")


if __name__ == "__main__":
    # Configure logging
    logs_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "logs")
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
