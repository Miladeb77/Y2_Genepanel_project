import requests
import pandas as pd
import json
import sqlite3

# Base URL for PanelApp API
server = "https://panelapp.genomicsengland.co.uk"
panels_url = f"{server}/api/v1/panels/"
headers = {"Content-Type": "application/json"}

# Initialize list to store detailed panel and gene information
all_panel_gene_data = []
page = 1

# Step 1: Retrieve all panels
while True:
    response = requests.get(panels_url, headers=headers, params={"page": page})
    if response.status_code == 200:
        data = response.json()
        panels = data.get("results", [])
        
        for panel in panels:
            
            r_codes = [disorder for disorder in panel.get("relevant_disorders", []) if disorder.startswith("R")]
            if r_codes:
                panel_id = panel["id"]
            
            # Step 2: Fetch detailed panel and gene information for each panel
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
                    "relevant_disorders": ', '.join(panel_detail_data.get("relevant_disorders", [])),
                    "number_of_genes": panel_detail_data["stats"].get("number_of_genes", 0),
                    "number_of_strs": panel_detail_data["stats"].get("number_of_strs", 0),
                    "number_of_regions": panel_detail_data["stats"].get("number_of_regions", 0),
                    "types": json.dumps(panel_detail_data.get("types", []))  # Save as JSON for more complex data
                }
                
                # Extract gene information within the panel
                for gene in panel_detail_data.get("genes", []):
                    gene_data = {
                        "gene_symbol": gene["entity_name"],
                        "entity_type": gene["entity_type"],
                        "confidence_level": gene["confidence_level"],
                        "penetrance": gene.get("penetrance"),
                        "mode_of_pathogenicity": gene.get("mode_of_pathogenicity"),
                        "publications": ', '.join(gene.get("publications", [])),
                        "evidence": ', '.join(gene.get("evidence", [])),
                        "phenotypes": ', '.join(gene.get("phenotypes", [])),
                        "mode_of_inheritance": gene.get("mode_of_inheritance"),
                        "transcript": gene.get("transcript"),
                    }
                    
                    # Extract additional fields from gene_data
                    gene_data_details = gene.get("gene_data", {})
                    ensembl_data = gene_data_details.get("ensembl_genes", {})

                    # Check if ensembl_data is a dictionary
                    gene_data_flat = {
                        "gene_alias": ', '.join(gene_data_details.get("alias", [])) if gene_data_details.get("alias") else "",
                        "gene_biotype": gene_data_details.get("biotype"),
                        "gene_hgnc_id": gene_data_details.get("hgnc_id"),
                        "gene_name": gene_data_details.get("gene_name"),
                        "gene_omim": ', '.join(gene_data_details.get("omim_gene", []) if gene_data_details.get("omim_gene") else []),
                        "gene_symbol": gene_data_details.get("gene_symbol"),
                        "gene_hgnc_symbol": gene_data_details.get("hgnc_symbol"),
                        "gene_hgnc_release": gene_data_details.get("hgnc_release"),
                        "gene_hgnc_date_symbol_changed": gene_data_details.get("hgnc_date_symbol_changed"),
                        "gene_ensembl_GRch37": ensembl_data.get("GRch37", {}).get("82", {}).get("location") if isinstance(ensembl_data, dict) else None,
                        "gene_ensembl_GRch38": ensembl_data.get("GRch38", {}).get("90", {}).get("location") if isinstance(ensembl_data, dict) else None,
                        "gene_ensembl_id_GRch37": ensembl_data.get("GRch37", {}).get("82", {}).get("ensembl_id") if isinstance(ensembl_data, dict) else None,
                        "gene_ensembl_id_GRch38": ensembl_data.get("GRch38", {}).get("90", {}).get("ensembl_id") if isinstance(ensembl_data, dict) else None,
                    }
                    
                    # Combine panel, gene, and gene_data details into a single dictionary
                    combined_data = {**panel_info, **gene_data, **gene_data_flat}
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

# Ensure all columns are in basic types, like str, int, or float
for col in panel_gene_df.columns:
    if panel_gene_df[col].dtype == "object":
        panel_gene_df[col] = panel_gene_df[col].astype(str)

#Save to database
# conn = sqlite3.connect("panelapp.db")
# panel_gene_df.to_sql("panel_info", conn, if_exists="replace", index=False)
# conn.close()

# Display the first few rows of the DataFrame
#panel_gene_df.head()
