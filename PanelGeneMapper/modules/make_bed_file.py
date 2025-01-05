import requests
import logging
import sqlite3
import csv
import json
import glob
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import pandas as pd
from retrieve_gene_local_db import get_archive_dir, get_databases_dir, connect_and_join_databases,  retrieve_latest_panelapp_db

# Set up logging
# Define log directory two levels up
log_dir = os.path.join("..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "make_bed_file.log")

logging.basicConfig(
    level=logging.DEBUG,
    filename=log_file,
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)

# SQLite database for caching
output_dir = os.path.join("..", "output")
os.makedirs(output_dir, exist_ok=True)
DB_NAME = os.path.join(output_dir, "gene_data.db")
archive_folder = get_archive_dir()

def create_local_db():
    """
    Create a local SQLite database to cache exon data.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gene_exons (
            gene_id TEXT PRIMARY KEY,
            exon_data TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def cache_exon_data(gene_id, exon_data):
    """
    Cache exon data in the SQLite database.

    Parameters
    ----------
    gene_id : str
        Ensembl gene ID.
    exon_data : str
        Exon data as a JSON string.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO gene_exons (gene_id, exon_data) VALUES (?, ?)",
        (gene_id, exon_data),
    )
    conn.commit()
    conn.close()

def fetch_cached_data(gene_id):
    """
    Fetch exon data from the SQLite database.

    Parameters
    ----------
    gene_id : str
        Ensembl gene ID.

    Returns
    -------
    str or None
        Cached exon data as a JSON string, or None if not found.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT exon_data FROM gene_exons WHERE gene_id = ?", (gene_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def extract_ensembl_ids_from_csv(csv_file):
    """
    Extract distinct Ensembl gene IDs from a CSV file.

    Parameters
    ----------
    csv_file : str
        Path to the input CSV file.

    Returns
    -------
    list
        List of unique Ensembl gene IDs.
    """
    ensembl_ids = set()

    try:
        logging.info(f"Loading Ensembl gene IDs from CSV file: {csv_file}")
        df = pd.read_csv(csv_file)

        if "gene_ensembl_id_GRch38" not in df.columns:
            logging.error("CSV file does not contain the required 'gene_ensembl_id_GRch38' column.")
            return []

        ensembl_ids.update(df["gene_ensembl_id_GRch38"].dropna().unique())
        logging.info(f"Extracted {len(ensembl_ids)} unique Ensembl gene IDs from the CSV file.")
    except Exception as e:
        logging.error(f"An error occurred while extracting Ensembl IDs from the CSV file: {e}")

    return list(ensembl_ids)

def extract_ensembl_ids_with_join(patient_db=None, r_code=None, patient_id=None):
    """
    Extract distinct Ensembl gene IDs by joining data from patient_database and PanelApp databases.

    Parameters
    ----------
    patient_db : str, optional
        Path to the patient database. Defaults to the 'patient_database.db' in the databases directory.
    r_code : str, optional
        Clinical ID for filtering patient data.
    patient_id : str, optional
        Patient ID for filtering patient data.

    Returns
    -------
    list
        List of unique Ensembl gene IDs.
    """
    ensembl_ids = set()

    # Resolve the patient database path if not provided
    if patient_db is None:
        patient_db = os.path.join(get_databases_dir(), "patient_database.db")

    try:
        # Load patient data from the patient database
        with sqlite3.connect(patient_db) as patient_conn:
            patient_query = "SELECT DISTINCT clinical_id, panel_retrieved_date FROM patient_data"
            params = []
            if r_code:
                patient_query += " WHERE clinical_id = ?"
                params.append(r_code)
            elif patient_id:
                patient_query += " WHERE patient_id = ?"
                params.append(patient_id)

            patient_df = pd.read_sql_query(patient_query, patient_conn, params=params)

        if patient_df.empty:
            logging.warning("No matching patient data found.")
            return list(ensembl_ids)

        # Retrieve unique panel_retrieved_dates
        unique_dates = patient_df["panel_retrieved_date"].unique()

        for date in unique_dates:
            # Filter patient data for the current date
            filtered_patients = patient_df[patient_df["panel_retrieved_date"] == date]["clinical_id"].tolist()

            if not filtered_patients:
                logging.warning(f"No patients found for date: {date}")
                continue

            # Construct the expected PanelApp database file path
            panelapp_file = f"panelapp_v{date.replace('-', '')}.db"
            panelapp_path = os.path.join(get_databases_dir(), panelapp_file)

            # If the database file is not found, fall back to the archive folder
            if not os.path.isfile(panelapp_path):
                logging.info(f"PanelApp database not found in main directory for date: {date}. Checking archive...")
                panelapp_path, _ = retrieve_latest_panelapp_db(
                    archive_folder=get_archive_dir(),
                    panelapp_db=os.path.join(get_databases_dir(), panelapp_file)
                )

            # Load PanelApp data and perform the join
            with sqlite3.connect(panelapp_path) as panelapp_conn:
                query = f"""
                SELECT DISTINCT gene_ensembl_id_GRch38
                FROM panel_info
                WHERE relevant_disorders IN ({",".join(["?"] * len(filtered_patients))})
                """
                result = pd.read_sql_query(query, panelapp_conn, params=filtered_patients)

                # Add unique Ensembl IDs to the set
                ensembl_ids.update(result["gene_ensembl_id_GRch38"].dropna().tolist())

    except Exception as e:
        logging.error(f"An error occurred during extraction: {e}")

    return list(ensembl_ids)


def get_mane_exon_data(ensembl_id, species, server, headers):
    """
    Retrieve MANE Select exon data for a gene using the Ensembl API, with caching.
    """
    # Check the cache first
    cached_data = fetch_cached_data(ensembl_id)
    if cached_data:
        logging.info(f"Cache hit for {ensembl_id}.")
        return json.loads(cached_data)  # Parse JSON string into a Python dictionary

    url = f"{server}/overlap/id/{ensembl_id}"
    params = {"feature": "transcript", "species": species}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.ok:
            transcripts = response.json()
            if not isinstance(transcripts, list):
                logging.error(f"Unexpected response format for {ensembl_id}: {transcripts}")
                return None

            for transcript in transcripts:
                if "MANE_Select" in transcript.get("tag", []):
                    exon_response = requests.get(
                        f"{server}/overlap/id/{transcript['id']}",
                        headers=headers,
                        params={"feature": "exon"},
                        timeout=10,
                    )
                    if exon_response.ok:
                        exons = exon_response.json()
                        if not isinstance(exons, list):
                            logging.error(f"Unexpected exon data format for {ensembl_id}: {exons}")
                            return None

                        result = {
                            "seq_region_name": transcript.get("seq_region_name", "N/A"),
                            "gene_id": ensembl_id,
                            "gene_name": transcript.get("external_name", "N/A"),
                            "transcript_id": transcript["id"],
                            "transcript_type": "MANE_Select",
                            "exons": exons,
                        }
                        cache_exon_data(ensembl_id, json.dumps(result))
                        return result
                    else:
                        logging.error(f"Failed to fetch exon data for transcript {transcript['id']}: {exon_response.text}")
        else:
            logging.error(f"Failed to fetch data for {ensembl_id}. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error fetching data for {ensembl_id}: {e}")

    return None


def write_bed_file(data_list, output_file):
    """
    Write MANE Select exons to a BED file.
    """
    logging.info(f"Writing to BED file {output_file}.")
    try:
        with open(output_file, "w") as bed_file:
            for data in data_list:
                if not isinstance(data, dict) or "exons" not in data:
                    logging.warning(f"Skipping invalid data entry: {data}")
                    continue

                for exon in data["exons"]:
                    chrom = f"chr{data.get('seq_region_name', 'unknown')}"
                    start = exon.get("start", 0) - 1
                    end = exon.get("end", 0)
                    gene_name = data.get("gene_name", "unknown")
                    gene_id = data.get("gene_id", "unknown")
                    transcript_type = data.get("transcript_type", "unknown")
                    bed_file.write(f"{chrom}\t{start}\t{end}\t{gene_name}\t{gene_id}\t{transcript_type}\n")
    except IOError as e:
        logging.error(f"Error writing to file {output_file}: {e}")


def fetch_all_data(gene_ids, species, server, headers):
    """
    Fetch MANE Select exon data for multiple genes using multithreading.
    """
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(get_mane_exon_data, ensembl_id, species, server, headers)
            for ensembl_id in gene_ids
        ]
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

# def main():
#     """
#     Main function to extract Ensembl gene IDs, fetch MANE Select exon data, and write to a BED file.
#     """
#     parser = argparse.ArgumentParser(description="Make BED file from gene list or database.")
#     parser.add_argument("--csv_file", type=str, help="Path to the gene list CSV file.", required=False)
#     parser.add_argument("--r_code", type=str, help="Clinical ID to filter data.", required=False)
#     parser.add_argument("--patient_id", type=str, help="Patient ID to filter data.", required=False)

#     args = parser.parse_args()

    
#     output_file = os.path.join("..", "..", "output", "gene_exons.bed")
#     species = "homo_sapiens"
#     server = "https://rest.ensembl.org"
#     headers = {"Content-Type": "application/json"}

#     create_local_db()


#     # Extract Ensembl gene IDs
#     if args.csv_file:
#         # Extract from CSV if provided
#         ensembl_gene_ids = extract_ensembl_ids_from_csv(args.csv_file)
#     else:
#         # Extract using database
#         ensembl_gene_ids = extract_ensembl_ids_with_join(
#             patient_db=os.path.join("..", "..", "databases", "patient_database.db"),
#             r_code=args.r_code,
#             patient_id=args.patient_id,
#         )
#     data_list = fetch_all_data(ensembl_gene_ids, species, server, headers)
#     write_bed_file(data_list, output_file)
    



# if __name__ == "__main__":
#     main()


