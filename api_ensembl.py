import requests  # Import the requests library to make HTTP requests.
import json  # Import the json library to handle JSON data (commonly used in APIs).

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
    
    # Make the API request using the GET method.
    response = requests.get(gene_url, headers=headers)
    
    #  If we have successfully connected to the Ensembl API, start retrieving required data and writing to BED file. (status code 200).
    if response.ok:
        # Convert the JSON response from the API into a Python dictionary and return it.
        return response.json()
    else:
        # Log an error if the request fails.
        log_error(gene_symbol, response)
        return None  # Return None to indicate failure.

def write_bed_file(gene_list, species, server, headers, output_file="genes_coordinates.bed"):
    """
    Write the genomic coordinates of genes to a BED file.
    
    Arguments:
        gene_list: A list of gene symbols.
        species: The species name.
        server: The URL of the Ensembl REST API.
        headers: HTTP headers for the API request.
        output_file: The name of the output BED file ("genes_coordinates.bed").
    """
    # Open a new BED file named genomics_coordinates.bed. this has write permissions and will create a new file or overwrite an existing one.
    with open(output_file, "w") as bed_file:
        # Do a for loop which will loop through each gene in the gene_list input and for each, request the required data from the Ensembl API.
        for gene_symbol in gene_list:
            # Fetch data for the current gene using the get_ensembl_data function.
            gene_data = get_ensembl_data(gene_symbol, species, server, headers)
            
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
                bed_file.write(f"{chrom}\t{gene_start}\t{gene_end}\t{gene_name}\n")
    
    # Print a message to indicate that the BED file was created successfully.
    print(f"BED file '{output_file}' created successfully.")

def log_error(gene_symbol, response):
    """
    Log an error message when the API request fails.
    
    Arguments:
        gene_symbol (str): The name of the gene that caused the error.
        response (requests.Response): The HTTP response object from the failed API request.
    """
    # Print an error message showing the gene symbol and the HTTP status code/reason.
    print(f"Error fetching data for gene {gene_symbol}: {response.status_code} - {response.reason}")

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
    
    # Prompt the user to enter gene symbols separated by commas.
    # Example input: "BRCA2,TP53,EGFR"
    gene_input = input("Enter gene symbols separated by commas (e.g., BRCA2,TP53,EGFR): ")
    # Split the input string into a list of gene symbols, removing extra spaces from each gene and ignoring empty values.
    gene_list = [gene.strip() for gene in gene_input.split(",") if gene.strip()]
    
    # If the gene list is empty (e.g., the user didn't enter anything), exit the program.
    if not gene_list:
        print("No gene symbols provided. Exiting.")
        return  # Exit the program.
    
    # Call the write_bed_file function to fetch gene data and save it to a BED file.
    write_bed_file(gene_list, species, server, headers)

# If this script is being run directly (not imported as a module), execute the main function.
# This ensures that the main() function runs only when the script is executed directly,
# and not when it is imported into another script. This makes the script reusable and prevents
# unintended execution of the main logic when used as part of a larger program.
if __name__ == "__main__":
    main()