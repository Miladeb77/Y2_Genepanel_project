import requests
import pandas as pd
import json
import sqlite3
import os
from datetime import datetime

# Set the working directory to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# This extracts the data from panelapp API
server = "https://panelapp.genomicsengland.co.uk"
panels_url = f"{server}/api/v1/panels/"
headers = {"Content-Type": "application/json"}

# Initialize list to store detailed panel and gene information
all_panel_gene_data = []
page = 1

# Step 1: Retrieve all panels with relevant disorders starting with "R"
while True:
    response = requests.get(panels_url, headers=headers, params={"page": page})
    if response.status_code == 200:
        data = response.json()
        panels = data.get("results", [])
        
        for panel in panels:
            r_codes = [disorder for disorder in panel.get("relevant_disorders", []) if disorder.startswith("R")]
            if r_codes:
                panel_id = panel["id"]
                
                # Step 2: Fetch detailed panel and gene information for each filtered panel
                panel_detail_url = f"{server}/api/v1/panels/{panel_id}/"
                panel_detail_response = requests.get(panel_detail_url, headers=headers)
                
                if panel_detail_response.status_code == 200:
                    panel_detail_data = panel_detail_response.json()
                    
                    panel_info = {
                        "panel_id": panel_detail_data["id"],
                        "hash_id": panel_detail_data.get("hash_id"),
                        "name": panel_detail_data["name"],
                        "disease_group": panel_detail_data.get("disease_group", ""),
                        "disease_sub_group": panel_detail_data.get("disease_sub_group", ""),
                        "status": panel_detail_data["status"],
                        "version": panel_detail_data["version"],
                        "version_created": panel_detail_data["version_created"],
                        "relevant_disorders": r_codes,
                        "number_of_genes": panel_detail_data["stats"].get("number_of_genes", 0),
                        "number_of_strs": panel_detail_data["stats"].get("number_of_strs", 0),
                        "number_of_regions": panel_detail_data["stats"].get("number_of_regions", 0),
                        "types": [ptype.get("name") for ptype in panel_detail_data.get("types", [])]
                    }
                    
                    for gene in panel_detail_data.get("genes", []):
                        gene_data = {
                            "gene_symbol": gene["entity_name"],
                            "entity_type": gene["entity_type"],
                            "confidence_level": gene["confidence_level"],
                            "penetrance": gene.get("penetrance"),
                            "mode_of_pathogenicity": gene.get("mode_of_pathogenicity"),
                            "publications": gene.get("publications", []),
                            "evidence": gene.get("evidence", []),
                            "phenotypes": gene.get("phenotypes", []),
                            "mode_of_inheritance": gene.get("mode_of_inheritance"),
                            "transcript": gene.get("transcript"),
                        }
                        
                        combined_data = {**panel_info, **gene_data}
                        all_panel_gene_data.append(combined_data)
                else:
                    print(f"Failed to retrieve detailed info for panel {panel_id}")
        
        if data.get("next") is None:
            break
        else:
            page += 1
    else:
        print(f"Failed to retrieve data on page {page}")
        break

# Convert the data to a DataFrame
panel_gene_df = pd.DataFrame(all_panel_gene_data)

# Format lists and dictionaries
list_columns = ["relevant_disorders", "publications", "evidence", "phenotypes", "transcript"]
for col in list_columns:
    panel_gene_df[col] = panel_gene_df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else "")

dict_columns = ["types"]
for col in dict_columns:
    panel_gene_df[col] = panel_gene_df[col].apply(lambda x: json.dumps(x) if isinstance(x, dict) else "")

for col in panel_gene_df.columns:
    if panel_gene_df[col].dtype == "object":
        panel_gene_df[col] = panel_gene_df[col].astype(str)

# Generate a versioned database name with date and time
date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
database_name = f"panelapp_v{date_str}.db"

# Archive previous databases
archive_folder = os.path.join(script_dir, "archive_databases")
os.makedirs(archive_folder, exist_ok=True)
for db_file in os.listdir(script_dir):
    if db_file.startswith("panelapp_v") and db_file.endswith(".db") and db_file != database_name:
        os.rename(db_file, os.path.join(archive_folder, db_file))
        os.system(f"gzip {os.path.join(archive_folder, db_file)}")  # Compress the database

# Save the new database in the current working directory
conn = sqlite3.connect(database_name)
panel_gene_df.to_sql("panel_info", conn, if_exists="replace", index=False)
conn.close()

print(f"Data saved to SQLite database '{database_name}'")