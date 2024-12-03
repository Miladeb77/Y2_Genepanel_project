import requests
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.DEBUG,
    filename="program.log",
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)

def get_ensembl_data(ensembl_id, species, server, headers):
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

def fetch_all_genes_data(gene_ids, species, server, headers):
    """
    Fetch data for multiple genes in parallel using ThreadPoolExecutor.
    """
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limiting max concurrent threads to 10
        futures = {executor.submit(get_ensembl_data, gene_id, species, server, headers): gene_id for gene_id in gene_ids}
        results = []
        for future in as_completed(futures):
            gene_id = futures[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
                else:
                    logging.error(f"Failed to retrieve data for gene {gene_id}.")
            except Exception as e:
                logging.error(f"Error fetching data for gene {gene_id}: {e}")
        return results

def main():
    server = "https://rest.ensembl.org"
    species = "homo_sapiens"
    headers = {"Content-Type": "application/json"}
    
    table_id = ["ENSG00000139618", "ENSG00000183765", "ENSG00000168235", "ENSG00000141510"]  # Add more gene IDs as needed
    
    if not table_id:
        logging.warning("No Ensembl Gene IDs provided. Exiting.")
        return
    
    JSON_output = fetch_all_genes_data(table_id, species, server, headers)
    
    if JSON_output:
        output_file = "gene_exons_coordinates_with_type.bed"
        write_bed_file(JSON_output, output_file)
    else:
        logging.error("No valid data retrieved for any Ensembl Gene ID.")

if __name__ == "__main__":
    main()