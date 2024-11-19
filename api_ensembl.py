import requests
import pandas as pd
import json
import sqlite3

# Base URL for PanelApp API
server = "https://rest.ensembl.org"

# Specify the species and gene symbol (replace "homo_sapiens" and "BRAF" as needed)
species = "homo_sapiens"
gene_symbol = "BRAF"

# Define the endpoint
endpoint = f"/lookup/symbol/{species}/{gene_symbol}"

# Full URL
url = f"{server}{endpoint}"


# Headers
headers = {"Content-Type": "application/json"}


# Make the API call
response = requests.get(url, headers=headers)

# Check and process the response
if response.ok:
    # Parse JSON response
    gene_data = response.json()

    # Extract desired information
    chrom = gene_data.get("seq_region_name")  # Chromosome name
    start = gene_data.get("start")  # Start location
    end = gene_data.get("end")  # End location
    gene_name = gene_data.get("display_name")  # Gene name
    print(f"Gene: {gene_name}, Chromosome: {chrom}, Start: {start}, End: {end}")
else:
    print(f"Error: {response.status_code} - {response.reason}")