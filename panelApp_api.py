import requests
import pandas as pd
import sys

def get_panel_app_list():
    """
    Queries the PanelApp API to return details on all signed-off panels.
    
    :return: Pandas dataframe, Columns: id, hash_id, name, disease_group, disease_sub_group, status, version, 
             version_created, relevant_disorders, types, stats.number_of_genes, stats.number_of_strs, 
             stats.number_of_regions
    :rtype: pandas.DataFrame
    """
    server = "https://panelapp.genomicsengland.co.uk"
    ext = "/api/v1/panels/signedoff/"

    # Initial request to the API
    r = requests.get(server + ext, headers={"Content-Type": "application/json"})
    if not r.ok:
        print("Error with initial API request.")
        r.raise_for_status()
        sys.exit()

    # Parse the JSON and check for expected keys
    data = r.json()
    if "results" not in data:
        print("No 'results' key found in API response.")
        return pd.DataFrame()  # Return an empty DataFrame if no results found

    # Create initial DataFrame from the first page
    GEL_panel_app_df = pd.json_normalize(data, record_path=["results"])
    print(f"Initial DataFrame created with {len(GEL_panel_app_df)} rows.")

    # Check for pagination and iterate over remaining pages if needed
    while data.get("next") is not None:
        next_page = data["next"]
        print(f"Fetching next page: {next_page}")
        
        r = requests.get(next_page, headers={"Content-Type": "application/json"})
        if not r.ok:
            print(f"Error fetching page: {next_page}")
            r.raise_for_status()
            sys.exit()
        
        data = r.json()
        if "results" in data:
            page_df = pd.json_normalize(data, record_path=["results"])
            GEL_panel_app_df = pd.concat([GEL_panel_app_df, page_df], ignore_index=True)
            print(f"Appended data from page with {len(page_df)} rows. Total rows now: {len(GEL_panel_app_df)}")
        else:
            print(f"No 'results' found on page {next_page}. Ending pagination.")
            break

    return GEL_panel_app_df

GEL_panel_app_df = get_panel_app_list()

GEL_panel_app_df.head()
