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
    Parameters:
        csv_file: Path to the CSV file.
    Returns:
        A list of Ensembl gene IDs.
    """
    logging.info(f"Reading Ensembl gene IDs from {csv_file}.")  # Log the start of the process to read the Ensembl gene IDs from the provided CSV file.
    ensembl_ids = set()  # Initialize an empty set to store unique Ensembl gene IDs. Using a set ensures uniqueness automatically.
    
    try:
        with open(csv_file, "r") as file:  # Try to open the specified CSV file in read mode.
            reader = csv.DictReader(file)  # Create a DictReader object to read the CSV file. This treats the first row as the header and allows access to each field by its name.
            for row in reader:  # Loop through each row in the CSV file.
                ensembl_id = row.get("gene_ensembl_id_GRch38")  # Retrieve the Ensembl gene ID from the current row. The ID should be in the column named "gene_ensembl_id_GRch38".
                
                if ensembl_id:  # Check if the Ensembl ID is not None or an empty string.
                    ensembl_ids.add(ensembl_id)  # Add the Ensembl ID to the set, ensuring it is unique.
    
    except IOError as e:  # Catch any I/O errors, such as file not found or permission denied.
        logging.error(f"Error reading file {csv_file}: {e}")  # Log the error message with details about the file and the error.
    
    return list(ensembl_ids)  # Convert the set of unique Ensembl IDs back into a list and return it.


def get_ensembl_data(ensembl_id, species, server, headers):
    ''' 
    Request gene, transcript and exon data from Ensembl API endpoints in parallel. 
    Parameters:
        a) an ensembl ID representing the gene the data should be requested for.
        b) the species of the genome
        c) the server which hosts the data. In this context, this is the ensembl API.
        d) headers for the json file
    Returns: 
    If the API request is successful an API response in JSON format will be returned.
    '''
    # The endpoint for the gene data request.
    gene_endpoint = f"/lookup/id/{ensembl_id}"
    # The server hosting the gene data and endpoint. This is Ensembl.
    gene_url = f"{server}{gene_endpoint}"
    # Log that the API request is starting to fetch data from the Ensembl API for the given gene (the Ensembl ID that has been input).
    logging.info(f"Starting to fetch data from API for gene {ensembl_id} from {gene_url}.")

    try:
        # Start the API request and retrieve response
        response = requests.get(gene_url, headers=headers)
        # If there is a response
        if response.ok:
            # Retrieve response in JSON format
            gene_data = response.json()
            # Define the endpoint for the transcript data API request.
            transcript_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{gene_data['start']}-{gene_data['end']}?feature=transcript"
            # Define the URL hosting the transcript endpoint. This is Ensembl.
            transcript_url = f"{server}{transcript_endpoint}"

            # Make the API request and retrieve response
            transcript_response = requests.get(transcript_url, headers=headers)
            # If there is a response
            if transcript_response.ok:
                # Retrieve the response in JSON format
                transcripts = transcript_response.json()
                # If the transcripts variable isn't empty
                if transcripts:
                    # Create an empty list
                    gene_data['transcripts'] = []
                    # Loop through every transcript in the list
                    for transcript in transcripts:
                        # Get all of the tags for the transcript and turn them into a string
                        transcript_type = ", ".join(transcript.get("tag", []))
                        # Look for the MANE select transcript and if there is one
                        if "MANE_Select" in transcript_type:
                            # Define the endpoint for the exon data API request.
                            exon_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{transcript['start']}-{transcript['end']}?feature=exon"
                            # Define the URL hosting the exon endpoint. This is Ensembl.
                            exon_url = f"{server}{exon_endpoint}"
                            # Make the API request and retrieve response
                            exon_response = requests.get(exon_url, headers=headers)
                            # If there is a response
                            if exon_response.ok:
                                # Retrieve the response in JSON format
                                exons = exon_response.json()
                                # Add the transcript data to the transcript list that was created.
                                gene_data['transcripts'].append({
                                    "transcript_id": transcript["id"],  # Transcript ID
                                    "transcript_type": transcript_type,  # Transcript type
                                    "exons": exons  # Exon data retrieved from the API request
                                })
                    # Return the data in the list
                    return gene_data
                # Log if the transcripts variable was empty (meaning that no transcripts were found)
                else:
                    logging.info(f"No transcripts found for gene {ensembl_id}.")
            # Log if there was no response from the transcript data API request
            else:
                logging.error(f"Failed to fetch transcript data for gene {ensembl_id}.")
        # Log if there was no response from the gene data API request
        else:
            logging.error(f"Failed to fetch gene data for {ensembl_id}.")
    # Make an exception so that errors with HTTP requests are logged instead of them crashing the program.
    except requests.RequestException as e:
        logging.error(f"Error fetching data for gene {ensembl_id}: {e}")
    # Return nothing if any responses failed
    return None

def write_bed_file(JSON_output, output_file):
    ''' 
    Write the API request data to a BED file.
    Parameters:
        a) the output of the API request in JSON format for all genes
    Returns:
    An output BED file for all genes
    '''
    # Log that the write to BED file function has started running
    logging.info(f"Writing to BED file {output_file}.")
    
    try:
        # Open an output file that can be written to
        with open(output_file, "w") as bed_file:
            # For each gene in the JSON file output
            for gene_data in JSON_output:
                # If there is data
                if gene_data and 'transcripts' in gene_data:
                    # Get data for what chromsome the gene is on and format to include 'chr'
                    chrom = f"chr{gene_data.get('seq_region_name')}"
                    # Get the gene name
                    gene_name = gene_data.get("display_name")
                    # For every gene in the transcripts list
                    for transcript in gene_data['transcripts']:
                        # Get the transcript ID 
                        transcript_id = transcript.get("transcript_id")
                        # Get the transcript type
                        transcript_type = "MANE_Select" if "MANE_Select" in transcript.get("transcript_type", "") else ""
                        # If the transcript type is MANE Select
                        if transcript_type:
                            # For every exon in the transcript
                            for exon in transcript['exons']:
                                # Get the exon start position
                                exon_start = exon.get("start")
                                # Get the exon end position
                                exon_end = exon.get("end")
                                # If data has been retrieved for chromosome, gene name, transcript type, transcript ID and exon start and end
                                if chrom and exon_start and exon_end and gene_name and transcript_id and transcript_type:
                                    # Write a BED file in BED file format
                                    bed_file.write(f"{chrom}\t{exon_start}\t{exon_end}\t{gene_name}\t{transcript_id}\t{transcript_type}\n")
                                # If data was not retrieved log that there is incomplete data to write to a BED file
                                else:
                                    logging.warning(f"Incomplete data for {gene_name}. Skipping exon.")
    # Make an exception so that errors with writing to BED file are logged instead of them crashing the program.
    except IOError as e:
        logging.error(f"Error writing to file {output_file}: {e}")

def fetch_all_genes_data(gene_ids, species, server, headers):
    '''
    Fetch data via API requests for multiple genes in parallel using ThreadPoolExecutor.
    Parameters:
        a) the ID representing the gene the data should be requested for.
        b) the species of the genome
        c) the server which hosts the data. In this context, this is the ensembl API.
        d) headers for the json file
    Returns: 
    An output file with JSON data retrieved from the API for all genes.
    '''
    # List to store API responses in JSON format
    results = []
    
    # Use ThreadPoolExecutor to execute API requests concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        # For every gene ID in the list
        futures = [executor.submit(get_ensembl_data, ensembl_id, species, server, headers) for ensembl_id in gene_ids]
        # Process results as they are completed
        for future in as_completed(futures):
            # Get the result from the future
            result = future.result()
            # If the result is not None, append it to the results list
            if result:
                results.append(result)
    
    return results

def main():
    # Define the path to your CSV file containing the Ensembl gene IDs
    csv_file = "gene_list.csv"
    # Define the species and server used for the API calls (using ENSEMBL as an example)
    species = "hsapiens"  # Homo sapiens
    server = "https://rest.ensembl.org"
    # Define headers for the API request (with content-type set to application/json)
    headers = {"Content-Type": "application/json"}

    # Extract Ensembl gene IDs from the CSV file
    ensembl_gene_ids = extract_ensembl_ids(csv_file)

    # Fetch gene data from Ensembl
    gene_data_list = fetch_all_genes_data(ensembl_gene_ids, species, server, headers)

    # Write the data to a BED file
    output_file = "gene_data.bed"
    write_bed_file(gene_data_list, output_file)

if __name__ == "__main__":
    main()
