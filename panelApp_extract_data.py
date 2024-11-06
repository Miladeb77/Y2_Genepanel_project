import requests
import pandas as pd

#This extracts the data from panelapp api
# Base URL for PanelApp API
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
            # Filter for panels with relevant disorders containing "R" codes
            r_codes = [disorder for disorder in panel.get("relevant_disorders", []) if disorder.startswith("R")]
            if r_codes:
                panel_id = panel["id"]
                
                # Step 2: Fetch detailed panel and gene information for each filtered panel
                panel_detail_url = f"{server}/api/v1/panels/{panel_id}/"
                panel_detail_response = requests.get(panel_detail_url, headers=headers)
                
                if panel_detail_response.status_code == 200:
                    panel_detail_data = panel_detail_response.json()
                    
                    # Extract panel information
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
                    
                    # Extract gene information within the panel
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
                        
                        # Combine panel and gene data into a single dictionary
                        combined_data = {**panel_info, **gene_data}
                        all_panel_gene_data.append(combined_data)
                else:
                    print(f"Failed to retrieve detailed info for panel {panel_id}")
        
        # Check if there is a next page
        if data.get("next") is None:
            break
        else:
            page += 1
    else:
        print(f"Failed to retrieve data on page {page}")
        break

# Convert the data to a DataFrame
panel_gene_df = pd.DataFrame(all_panel_gene_data)

# Display the first few rows of the DataFrame
#print(panel_gene_df.head())
#len(panel_gene_df)
# Convert lists to comma-separated strings
list_columns = ["relevant_disorders", "publications", "evidence", "phenotypes", "transcript"]
for col in list_columns:
    panel_gene_df[col] = panel_gene_df[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else "")

# Convert dictionaries to JSON strings
dict_columns = ["types"]
for col in dict_columns:
    panel_gene_df[col] = panel_gene_df[col].apply(lambda x: json.dumps(x) if isinstance(x, dict) else "")

# Ensure all columns are in basic types, like str, int, or float
for col in panel_gene_df.columns:
    if panel_gene_df[col].dtype == "object":
        panel_gene_df[col] = panel_gene_df[col].astype(str)

# Save to SQLite database
# conn = sqlite3.connect("panelapp.db")
# panel_gene_df.to_sql("panel_info", conn, if_exists="replace", index=False)
# conn.close()

# print("Data saved to SQLite database 'panelapp.db'")
panel_gene_df.head()
