import requests  # Import the requests library to make HTTP requests.
import json  # Import the json library to handle JSON data (commonly used in APIs).
import logging  # Import logging module to handle logging throughout the program.

# Set up the logging level you want to be recorded and also the format of the logs.
logging.basicConfig(
    level=logging.DEBUG,  # The logging level that you want to be recorded.
    filename="program.log",  # This is the path to the file that the logs will be recorded in.
    encoding="utf-8",  # This means that the log file will accept and record typical English characters and other symbols if needed.
    filemode="a",  # Mode the file should be in. 'a' means that the file will be open for writing.
    format="{asctime} - {levelname} - {message}",  # This is the format of the messages in the log file, what they will look like.
    style="{",  # This makes sure the log uses string formatting.
    datefmt="%Y-%m-%d %H:%M",  # The date and time of errors will be recorded in the error log.
)

def get_ensembl_data(ensembl_id, species, server, headers):
    """
    Fetch gene, transcript, and exon data from the Ensembl REST API using the Ensembl Gene ID.
    """
    gene_endpoint = f"/lookup/id/{ensembl_id}"
    gene_url = f"{server}{gene_endpoint}"

    logging.info(f"Starting to fetch data from API for gene {ensembl_id} from {gene_url}.")

    try:
        response = requests.get(gene_url, headers=headers)
        if response.ok:
            gene_data = response.json()
            transcript_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{gene_data['start']}-{gene_data['end']}?feature=transcript"
            transcript_url = f"{server}{transcript_endpoint}"
            
            transcript_response = requests.get(transcript_url, headers=headers)
            if transcript_response.ok:
                transcripts = transcript_response.json()
                if transcripts:
                    gene_data['transcripts'] = []
                    for transcript in transcripts:
                        transcript_type = ", ".join(transcript.get("tag", []))
                        if "MANE_Select" in transcript_type:
                            exon_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{transcript['start']}-{transcript['end']}?feature=exon"
                            exon_url = f"{server}{exon_endpoint}"
                            exon_response = requests.get(exon_url, headers=headers)
                            if exon_response.ok:
                                exons = exon_response.json()
                                gene_data['transcripts'].append({
                                    "transcript_id": transcript["id"],
                                    "transcript_type": transcript_type,
                                    "exons": exons
                                })
                    return gene_data
                else:
                    logging.info(f"No transcripts found for gene {ensembl_id}.")
            else:
                logging.error(f"Failed to fetch transcript data for gene {ensembl_id}.")
        else:
            logging.error(f"Failed to fetch gene data for {ensembl_id}.")
    except requests.RequestException as e:
        logging.error(f"Error fetching data for gene {ensembl_id}: {e}")
    return None

def write_bed_file(JSON_output, output_file):
    """
    Write the genomic coordinates of exons to a BED file, focusing on MANE_Select transcripts.
    """
    logging.info(f"Writing to BED file {output_file}.")
    
    try:
        with open(output_file, "w") as bed_file:
            for gene_data in JSON_output:
                if gene_data and 'transcripts' in gene_data:
                    chrom = f"chr{gene_data.get('seq_region_name')}"
                    gene_name = gene_data.get("display_name")
                    
                    for transcript in gene_data['transcripts']:
                        transcript_id = transcript.get("transcript_id")
                        transcript_type = transcript.get("transcript_type")
                        
                        if "MANE_Select" in transcript_type:
                            for exon in transcript['exons']:
                                exon_start = exon.get("start")
                                exon_end = exon.get("end")
                                if chrom and exon_start and exon_end and gene_name and transcript_id and transcript_type:
                                    bed_file.write(f"{chrom}\t{exon_start}\t{exon_end}\t{gene_name}\t{transcript_id}\t{transcript_type}\n")
                                else:
                                    logging.warning(f"Incomplete data for {gene_name}. Skipping exon.")
    except IOError as e:
        logging.error(f"Error writing to file {output_file}: {e}")

def main():
    """
    Main function to drive the execution of the program.
    It coordinates fetching data from the Ensembl API and writing it to a BED file.
    """
    server = "https://rest.ensembl.org"
    species = "homo_sapiens"
    headers = {"Content-Type": "application/json"}
    
    # Ask for the Ensembl Gene IDs from the user, separated by commas
    table_id = ["ENSG00000139618","ENSG00000183765"]
    
    if not table_id:
        logging.warning("No Ensembl Gene IDs provided. Exiting.")
        return
    
    JSON_output = []
    
    for x in table_id:
        gene_data = get_ensembl_data(x, species, server, headers)
        if gene_data:
            JSON_output.append(gene_data)
        else:
            logging.error(f"Could not retrieve data for Ensembl Gene ID: {ensembl_id}")
    
    if JSON_output:
        output_file = "gene_exons_coordinates_with_type.bed"
        write_bed_file(JSON_output, output_file)
    else:
        logging.error("No valid data retrieved for any Ensembl Gene ID.")

if __name__ == "__main__":
    main()
