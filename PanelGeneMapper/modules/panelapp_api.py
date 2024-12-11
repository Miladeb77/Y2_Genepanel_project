import requests
import pandas as pd

def get_panel_app_list():
    """
    Queries the PanelApp API to return details on all signed-off Panels.
    """
    server = "https://panelapp.genomicsengland.co.uk"
    ext = "/api/v1/panels/"

    r = requests.get(server + ext, headers={"Content-Type": "application/json"})
    if not r.ok:
        r.raise_for_status()

    panel_app_df = pd.json_normalize(r.json(), record_path=["results"])
    all_dataframes = [panel_app_df]

    while r.json().get("next") is not None:
        r = requests.get(r.json()["next"], headers={"Content-Type": "application/json"})
        next_page_df = pd.json_normalize(r.json(), record_path=["results"])
        all_dataframes.append(next_page_df)

    panel_app_df = pd.concat(all_dataframes, ignore_index=True)
    return panel_app_df[["id", "version"]].rename(columns={"id": "panel_id"})
