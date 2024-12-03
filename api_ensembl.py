import requests  # Import the requests library to make HTTP requests.
import json  # Import the json library to handle JSON data (commonly used in APIs).
import logging # Import logging module which is needed to create an error log for this program
# set up the logging level you want to be recorded and also the format of the logs.
logging.basicConfig(
    level=logging.DEBUG, #the logging level that you want to be recorded
    filename="program.log", #this is the path to the file that the logs will be recorded in
    encoding="utf-8", #this means that the log file will accept and record typical English characters and other symbols if needed
    filemode="a", #mode the file should be in. 'a' means that the file will be open for writing.
    format="{asctime} - {levelname} - {message}", #this is the format of the messages in the log file, what they will look like.
    style="{", #this makes sure the log uses string formatting
    datefmt="%Y-%m-%d %H:%M", #the date and time of errors will be recorded in the error log
)


def get_ensembl_data(gene_symbol, species, server, headers):
    """
    Fetch gene data from the Ensembl REST API.
    
    Arguments:
        gene_symbol: The name of the gene to look up.
        species: The species name (e.g., "homo_sapiens" for humans).
        server: The URL of the Ensembl REST API (e.g., "https://rest.ensembl.org").
        headers: HTTP headers for the request, specifying the JSON format.

    Returns:
        dict: If the API request is successful, the function returns the gene data as a dictionary. This lets you access information like chromosome, start position, end position, and gene name using keys.
        None: If the API request fails (e.g., due to a network error or invalid gene name), the function returns None to indicate no data was retrieved.
    """

    # Define the API endpoint for looking up the gene symbol.
    gene_endpoint = f"/lookup/symbol/{species}/{gene_symbol}"  
        # This is the full URL for the location in the Ensembl API where we request the required data for each gene.
    gene_url = f"{server}{gene_endpoint}"  
        
    logging.info(f"Starting to fetch data from api for gene {gene_symbol} in species {species} from {gene_url}.")
    
    try:
        # Make the API request using the GET method.
        response = requests.get(gene_url, headers=headers)
                    
        #  If we have successfully connected to the Ensembl API, start retrieving required data and writing to BED file. (status code 200).
        if response.ok:
            logging.info(f"Successfully retrieved data from api for gene {gene_symbol}: {response.json()}")
                    # Convert the JSON response from the API into a Python dictionary and return it.
            return response.json()
        else:
            # Log an error if the request fails.
            logging.error(f"Failed to fetch data for gene {gene_symbol}. Status code: {response.status_code}, Reason: {response.reason}")
            return None  # Return None to indicate failure.
    except requests.RequestException as e:
        # log any exceptions from the requests module that happen during the request
        logging.error(f"An error occurred while fetching data from api for gene {gene_symbol}: {e}")
        return None
        



def write_bed_file(JSON_output, output_file):
    """
    Write the genomic coordinates of genes to a BED file.
    
    Arguments:
        gene_list: A list of gene symbols.
        species: The species name.
        server: The URL of the Ensembl REST API.
        headers: HTTP headers for the API request.
        output_file: The name of the output BED file ("genes_coordinates.bed").
    """
    logging.info(f"Starting to create BED file.")

    try:
        # Open a new BED file named genomics_coordinates.bed. this has write permissions and will create a new file or overwrite an existing one.
        with open(output_file, "w") as bed_file:
            logging.info(f"Successfully opened BED file named {output_file}.")
            # Do a for loop which will loop through each gene in the gene_list input and for each, request the required data from the Ensembl API.
            for gene_data in JSON_output:
                
                # If data was successfully retrieved for the gene:
                if gene_data:
                    # Extract the chromosome name.
                    chrom = f"chr{gene_data.get('seq_region_name')}"
                    # Extract the start position of the gene on the chromosome.
                    gene_start = gene_data.get("start")
                    # Extract the end position of the gene on the chromosome.
                    gene_end = gene_data.get("end")
                    # Extract the display name of the gene (same as gene_symbol).
                    gene_name = gene_data.get("display_name")
                    # Write the extracted data to the BED file in tab-separated format.
                    # BED format: chromosome, start, end, gene name.
                    if chrom and gene_start and gene_end and gene_name:
                        bed_file.write(f"{chrom}\t{gene_start}\t{gene_end}\t{gene_name}\n")
                    # Log a warning if no data was retrieved for the gene.
                    else:
                        logging.warning(f"Incomplete data for gene: {gene_data}")
                # Log a message indicating that the BED file was created successfully.
                else:
                    logging.warning("Skipping null gene data.")
        logging.info(f"BED file '{output_file}' created successfully.")
    except IOError as e:
        # Handle file I/O errors (e.g., permission issues, disk errors).
        logging.error(f"Failed to open or write to file '{output_file}': {e}")
        # Catch any other unexpected errors during the process.
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating BED file: {e}")
                    
def main():
    """
    Main function to execute the script logic.
    """
    # Define the Ensembl REST API server URL.
    server = "https://rest.ensembl.org"
    # Define the species name (e.g., "homo_sapiens" for humans).
    species = "homo_sapiens"
    # Define the headers for the API request. JSON format is required.
    headers = {"Content-Type": "application/json"}
    # Example input: "BRCA2,TP53,EGFR"
    input_genes = input("Enter gene symbols separated by commas (e.g., BRCA2,TP53,EGFR): ")
    
    # Prompt the user to enter gene symbols separated by commas.
    
    # Create empty list for reformatted gene list
    gene_list = []
    for gene in input_genes.split(","): #Splits the string into individual gene symbol strings using a comma as the delimiter.
        if gene.strip():  #Ensures the stripped string is not empty (filters out empty or whitespace-only entries).
            gene_list.append(gene.strip())  #Adds the cleaned gene symbol to the resulting list.

    # If the gene list is empty (e.g., the user didn't enter anything), exit the program.
    if not gene_list:
        logging.warning("No gene symbols provided. Exiting.")
        return  # Exit the program
    

    JSON_output = []
    for gene_symbol in gene_list:
        gene_data = get_ensembl_data(gene_symbol, species, server, headers)
        if gene_data:
            JSON_output.append(gene_data)

    # Specify the name of the output BED file.
    output_file = "genes_coordinates.bed"

    # Call the write_bed_file function to fetch gene data and save it to a BED file.
    write_bed_file(JSON_output,output_file)

    
    
# If this script is being run directly (not imported as a module), execute the main function.
# This ensures that the main() function runs only when the script is executed directly,
# and not when it is imported into another script. This makes the script reusable and prevents
# unintended execution of the main logic when used as part of a larger program.
if __name__ == "__main__":
    main()