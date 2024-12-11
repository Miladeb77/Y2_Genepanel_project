# Import the requests library to make HTTP requests.
import requests
# Import the json library to handle JSON data (this is commonly used in APIs).
import json
# Import logging module which is needed to log errors in this program.
import logging
# Import the CSV module to read data from the gene_list.csv file.
import csv
# Import ThreadPoolExecutor. This allows requests to be made to multiple APIs in parallel using different threads.
# as_completed makes sure that results from API requests across the threads are processed in the order they are completed.
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up the logging level to be recorded and also the format of the logs.
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level that you want to be recorded.
    filename="program.log",  # This is the path to the file that the logs will be recorded in.
    encoding="utf-8",  # This means that the log file will accept and record typical English characters and other symbols if needed.
    filemode="a",  # Mode the file should be in. 'a' means that the file will be open for writing.
    format="{asctime} - {levelname} - {message}",  # This is the format of the messages in the log file, what they will look like.
    style="{",  # This makes sure the log uses string formatting.
    datefmt="%Y-%m-%d %H:%M",  # The date and time of errors will be recorded in the error log.
)

def extract_ensembl_ids(csv_file):
    """
    Extract Ensembl gene IDs from the gene_list.csv file.

    Parameters
    ----------
    csv_file : str
        Path to the CSV file.

    Returns
    -------
    list of str
        A list of unique Ensembl gene IDs.
    """
    logging.info(f"Reading Ensembl gene IDs from {csv_file}.")  # Log the start of the process.
    ensembl_ids = set()  # Use a set to store unique Ensembl IDs for efficiency.

    try:
        with open(csv_file, "r") as file:  # Open the CSV file for reading.
            reader = csv.DictReader(file)  # Create a DictReader object to read the CSV file.
            for row in reader:  # Loop through each row in the CSV file.
                ensembl_id = row.get("gene_ensembl_id_GRch38")  # Retrieve Ensembl gene ID from the row.
                
                if ensembl_id:  # Check if the Ensembl ID is valid.
                    ensembl_ids.add(ensembl_id)  # Add the ID to the set of unique Ensembl IDs.

    except IOError as e:  # Handle file-related errors.
        logging.error(f"Error reading file {csv_file}: {e}")  # Log the error with file details.

    return list(ensembl_ids)  # Convert the set to a list and return.

def get_mane_exon_data(ensembl_id, species, server, headers):
    """
    Retrieve MANE Select exons for a gene using the overlap endpoint.

    Parameters
    ----------
    ensembl_id : str
        Ensembl gene ID.
    species : str
        Species for the API query (e.g., 'homo_sapiens').
    server : str
        Ensembl API server URL.
    headers : dict
        Headers for the HTTP request.

    Returns
    -------
    dict or None
        Dictionary with gene and MANE Select transcript data, or None if not found.
    """
    url = f"{server}/overlap/id/{ensembl_id}"  # Endpoint URL for the gene data request.
    params = {"feature": "transcript", "species": species}  # Query parameters for API request.

    try:
        response = requests.get(url, headers=headers, params=params)  # Send the API request.
        if response.ok:  # Check if the response is successful.
            transcripts = response.json()  # Parse the JSON response.
            for transcript in transcripts:  # Iterate over each transcript in the response.
                if "MANE_Select" in transcript.get("tag", []):  # Filter for MANE Select transcripts.
                    # Fetch exon data for the selected transcript.
                    exon_response = requests.get(
                        f"{server}/overlap/id/{transcript['id']}",
                        headers=headers,
                        params={"feature": "exon"},
                    )
                    if exon_response.ok:  # If exon data retrieval is successful.
                        exons = exon_response.json()  # Parse exon data as JSON.
                        return {
                            "seq_region_name": transcript["seq_region_name"],  # Chromosome or sequence region.
                            "gene_id": ensembl_id,  # Ensembl gene ID.
                            "gene_name": transcript.get("external_name", "N/A"),  # External gene name, default to 'N/A'.
                            "transcript_id": transcript["id"],  # Transcript ID.
                            "transcript_type": "MANE_Select",  # Transcript type.
                            "exons": exons,  # List of exons.
                        }
        else:  # Log an error if the request fails.
            logging.error(f"Failed to fetch data for {ensembl_id}: {response.text}")
    except requests.RequestException as e:  # Catch exceptions from the request.
        logging.error(f"Error fetching data for {ensembl_id}: {e}")  # Log the error with details.

    return None  # Return None if no data found or request failed.

def write_bed_file(data_list, output_file):
    """
    Write MANE Select exons to a BED file.

    Parameters
    ----------
    data_list : list of dict
        List of dictionaries with gene and exon data.
    output_file : str
        Path to the BED file.

    Returns
    -------
    None
    """
    logging.info(f"Writing to BED file {output_file}.")  # Log the start of writing to the BED file.
    try:
        with open(output_file, "w") as bed_file:  # Open the output file in write mode.
            for data in data_list:  # Iterate over each gene data in the list.
                if data and "exons" in data:  # Check if the data contains exon information.
                    for exon in data["exons"]:  # Iterate over each exon in the data.
                        chrom = f"chr{data['seq_region_name']}"  # Format chromosome name.
                        start = exon["start"] - 1  # Convert to 0-based start position for BED format.
                        end = exon["end"]  # End position for BED format.
                        gene_name = data["gene_name"]  # Gene name.
                        gene_id = data["gene_id"]  # Ensembl gene ID.
                        transcript_type = data["transcript_type"]  # Transcript type.
                        # Write exon information in BED file format.
                        bed_file.write(f"{chrom}\t{start}\t{end}\t{gene_name}\t{gene_id}\t{transcript_type}\n")

    except IOError as e:  # Handle I/O errors.
        logging.error(f"Error writing to file {output_file}: {e}")  # Log the error with file details.

def fetch_all_data(gene_ids, species, server, headers):
    """
    Fetch MANE Select exon data for multiple genes using multithreading.

    Parameters
    ----------
    gene_ids : list of str
        List of Ensembl gene IDs.
    species : str
        Species for the API query (e.g., 'homo_sapiens').
    server : str
        Ensembl API server URL.
    headers : dict
        Headers for the HTTP request.

    Returns
    -------
    list of dict
        A list of dictionaries with MANE Select exon data for each gene.
    """
    results = []  # Initialize the result list.
    with ThreadPoolExecutor(max_workers=10) as executor:  # Create a thread pool to manage requests.
        futures = [
            executor.submit(get_mane_exon_data, ensembl_id, species, server, headers)
            for ensembl_id in gene_ids
        ]  # Submit tasks for each gene ID.
        for future in as_completed(futures):  # Process results as they complete.
            result = future.result()  # Get the result from the future.
            if result:  # If a result was returned successfully.
                results.append(result)  # Add the result to the results list.

    return results  # Return the list of results.

def main():
    """
    Main function to extract Ensembl gene IDs, fetch MANE Select exon data,
    and write the data to a BED file.
    """
    csv_file = "gene_list.csv"  # Path to the CSV file containing Ensembl gene IDs.
    species = "homo_sapiens"  # Species for the API query.
    server = "https://rest.ensembl.org"  # Ensembl API server URL.
    headers = {"Content-Type": "application/json"}  # Headers for the API request.

    # Extract Ensembl gene IDs from the CSV file.
    ensembl_gene_ids = extract_ensembl_ids(csv_file)

    # Fetch MANE Select exon data for each gene.
    data_list = fetch_all_data(ensembl_gene_ids, species, server, headers)

    # Write the data to a BED file.
    output_file = "gene_exons.bed"
    write_bed_file(data_list, output_file)

if __name__ == "__main__":
    main()
