# Import the requests library to make HTTP requests.
import requests
# Import the json library to handle JSON data (this is commonly used in APIs).
import json
# Import logging module which is needed to log errors in this progam.
import logging
# import ThreadPoolEexecutor. This allows requests to be made to multiple APIs in parallel using different threads.
# as_completed makes sure that results from API requests across the threads are processed in the order they are completed.
from concurrent.futures import ThreadPoolExecutor, as_completed

# set up the logging level to be recorded and also the format of the logs.
logging.basicConfig(
    level=logging.DEBUG, #set the logging level that you want to be recorded.
    filename="program.log", #this is the path to the file that the logs will be recorded in.
    encoding="utf-8", #this means that the log file will accept and record typical English characters and other symbols if needed.
    filemode="a", #mode the file should be in. 'a' means that the file will be open for writing.
    format="{asctime} - {levelname} - {message}", #this is the format of the messages in the log file, what they will look like.
    style="{", #this makes sure the log uses string formatting.
    datefmt="%Y-%m-%d %H:%M",  #the date and time of errors will be recorded in the error log.
)

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
    #the endpoint for the gene data request.
    gene_endpoint = f"/lookup/id/{ensembl_id}"
    #the server hosting the gene data and endpoint. This is Ensembl.
    gene_url = f"{server}{gene_endpoint}"
    #log that the API request is starting to fetch data from the Ensembl API for the given gene (the Ensembl ID that has been input).
    logging.info(f"Starting to fetch data from API for gene {ensembl_id} from {gene_url}.")

    try:
        #start the API request and retrieve response
        response = requests.get(gene_url, headers=headers)
        #if there is a response
        if response.ok:
            #retrieve response in JSON format
            gene_data = response.json()
            #define the endpoint for the transcript data API request.
            transcript_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{gene_data['start']}-{gene_data['end']}?feature=transcript"
            #define the URL hosting the transcript endpoint. This is Ensembl.
            transcript_url = f"{server}{transcript_endpoint}"

            #make the API request and retrieve response
            transcript_response = requests.get(transcript_url, headers=headers)
            #if there is a response
            if transcript_response.ok:
                #retrieve the response in JSON format
                transcripts = transcript_response.json()
                #if the transcripts variable isn't empty
                if transcripts:
                    #create an empty list
                    gene_data['transcripts'] = []
                    #Loop through every transcript in the list
                    for transcript in transcripts:
                        #get all of the tags for the transcript and turn them into a string
                        transcript_type = ", ".join(transcript.get("tag", []))
                        #Look for the MANE select transcript and if there is one
                        if "MANE_Select" in transcript_type:
                            #define the endpoint for the exon data API request.
                            exon_endpoint = f"/overlap/region/{species}/{gene_data['seq_region_name']}:{transcript['start']}-{transcript['end']}?feature=exon"
                            #define the URL hosting the exon endpoint. This is Ensembl.
                            exon_url = f"{server}{exon_endpoint}"
                            #make the API request and retrieve response
                            exon_response = requests.get(exon_url, headers=headers)
                            #if there is a response
                            if exon_response.ok:
                                #retrieve the response in JSON format
                                exons = exon_response.json()
                                #add the transcript data to the transcript list that was created.
                                gene_data['transcripts'].append({
                                    "transcript_id": transcript["id"], #transcript ID
                                    "transcript_type": transcript_type, #transcript type
                                    "exons": exons #exon data retrieved from the API request
                                })
                    #return the data in the list
                    return gene_data
                #log if the transcripts variable was empty (meaning that no transcripts were found)
                else:
                    logging.info(f"No transcripts found for gene {ensembl_id}.")
            #log if there was no response from the transcript data API request
            else:
                logging.error(f"Failed to fetch transcript data for gene {ensembl_id}.")
        #log if there was no response from the gene data API request
        else:
            logging.error(f"Failed to fetch gene data for {ensembl_id}.")
    #make an exception so that errors with HTTP requests are logged instead of them crashing the program.
    except requests.RequestException as e:
        logging.error(f"Error fetching data for gene {ensembl_id}: {e}")
    #return nothing if any responses failed
    return None

def write_bed_file(JSON_output, output_file):
    ''' 
    Write the API request data to a BED file.
    Parameters:
        a) the output of the API request in JSON format for all genes
    Returns:
    An ouput BED file for all genes
    '''
    #log that the write to BED file function has started running
    logging.info(f"Writing to BED file {output_file}.")
    
    try:
       #open an output file that can be written to
        with open(output_file, "w") as bed_file:
            #for each gene in the JSON file output
            for gene_data in JSON_output:
                #if there is data
                if gene_data and 'transcripts' in gene_data:
                    #get data for what chromsome the gene is on and format to include 'chr'
                    chrom = f"chr{gene_data.get('seq_region_name')}"
                    #get the gene name
                    gene_name = gene_data.get("display_name")
                    #for every gene in the transcripts list
                    for transcript in gene_data['transcripts']:
                        #get the transcript ID 
                        transcript_id = transcript.get("transcript_id")
                        #get the transcript type
                        transcript_type = transcript.get("transcript_type")
                        #if the transcript type is MANE Select
                        if "MANE_Select" in transcript_type:
                            #for every exon in the transcript
                            for exon in transcript['exons']:
                                #get the exon start position
                                exon_start = exon.get("start")
                                #get the exon end position
                                exon_end = exon.get("end")
                                #if data has been retrieved for chromosome, gene name, transcript type, transcript ID and exon start and end
                                if chrom and exon_start and exon_end and gene_name and transcript_id and transcript_type:
                                    #write a BED file in BED file format
                                    bed_file.write(f"{chrom}\t{exon_start}\t{exon_end}\t{gene_name}\t{transcript_id}\t{transcript_type}\n")
                                #if data was not retrieved log that there is incomplete data to write to a BED file
                                else:
                                    logging.warning(f"Incomplete data for {gene_name}. Skipping exon.")
    #make an exception so that errors with writing to BED file are logged instead of them crashing the program.
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
    A list of results containing data from the multiple API requests.
    '''
    #use 10 threads in ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        #get data via ensembl API for multiple genes in parallel
        futures = {executor.submit(get_ensembl_data, gene_id, species, server, headers): gene_id for gene_id in gene_ids}
        #create an empty list for the results 
        results = []
        #iterate over the futures variable to see if any API requests for genes are completed
        for future in as_completed(futures):
            #if the request is completed for a gene, retrieve the gene ID
            gene_id = futures[future]
            try:
                #get the retrieved data for that gene
                data = future.result()
                #if there is data
                if data:
                    #add it to the results list that was created.
                    results.append(data)
                #log if data wasn't retrieved for a gene
                else:
                    logging.error(f"Failed to retrieve data for gene {gene_id}.")
            #Make an exception so that an error is logged instead of the error crashing the program.
            except Exception as e:
                logging.error(f"Error fetching data for gene {gene_id}: {e}")
        #return the results list
        return results

def main():
    #define the server hosting the Ensembl API
    server = "https://rest.ensembl.org"
    #define the species genome as human
    species = "homo_sapiens"
    #define the headers to make sure the request retrieves a JSON output
    headers = {"Content-Type": "application/json"}
    
    #Input gene list. These are the genes that we want to request data for.
    table_id = ["ENSG00000139618", "ENSG00000183765", "ENSG00000168235", "ENSG00000141510"]  # Add more gene IDs as needed
    
    #check if gene have been input. If not, stop the program.
    if not table_id:
        logging.warning("No Ensembl Gene IDs provided. Exiting.")
        return
    
    #Retrieve the data for the list of genes in JSON format.
    JSON_output = fetch_all_genes_data(table_id, species, server, headers)
    
    #If there is a JSON output
    if JSON_output:
        #name the output BED file
        output_file = "gene_exons_coordinates_with_type.bed"
        #write the output BED file
        write_bed_file(JSON_output, output_file)
    #log an error if no data was retrieved for an input gene
    else:
        logging.error("No valid data retrieved for any Ensembl Gene ID.")

#call the main function if the script is being run.
if __name__ == "__main__":
    main()