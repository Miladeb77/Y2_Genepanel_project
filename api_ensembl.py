# Import modules required for this script to run
import requests
import json

# Define the server URL needed to connect to Ensembl REST API.
server = "https://rest.ensembl.org"

# Define the species of the genome we need. This is needed to get the correct genome from Ensembl.
species = "homo_sapiens"

# Define a list of genes for testing purposes. This represents the user input which will be a list of genes for a specific R Code.
gene_list = ["BRCA2", "TP53", "EGFR"]

# Define the headers for the API request. The API request response needs to be in JSON format.
headers = {"Content-Type": "application/json"}

# Function to get gene data from Ensembl API
def get_gene_data(gene_symbol):
    # Define the endpoint. We need to look up the data in the Ensembl API using the gene symbol (gene name).
    gene_endpoint = f"/lookup/symbol/{species}/{gene_symbol}"
    
    # This is the full URL for the location in the Ensembl API where we request the required data for each gene.
    gene_url = f"{server}{gene_endpoint}"
    
    # Do the API request.
    gene_response = requests.get(gene_url, headers=headers)
    
    # If we have successfully connected to the Ensembl API, start retrieving required data and writing to BED file..
    if gene_response.ok:
        return gene_response.json()
    else:
        # If data was not retrieved correctly print an error. THIS NEEDS TO BE CHANGED TO LOGGING.
        print(f"Error fetching data for gene {gene_symbol}: {gene_response.status_code} - {gene_response.reason}")
        return None

# Function to extract relevant gene information
def extract_gene_info(gene_data):
    # Retrieve the relevant data from Ensembl API and put each into its own variable.
    chrom = gene_data.get("seq_region_name")  # Chromosome
    gene_start = gene_data.get("start")      # Gene start position
    gene_end = gene_data.get("end")          # Gene end position
    gene_name = gene_data.get("display_name")  # Gene name
    return chrom, gene_start, gene_end, gene_name

# Function to write gene data to a BED file
def write_to_bed_file(gene_info, bed_file):
    chrom, gene_start, gene_end, gene_name = gene_info
    # Write the retrieved data to the BED file (chrom, start, end, gene name)
    bed_file.write(f"{chrom}\t{gene_start}\t{gene_end}\t{gene_name}\n")

# Function to process the gene list and create the BED file
def create_bed_file(gene_list):
    # Open a new BED file named genomics_coordinates.bed. This has write permissions.
    with open("genes_coordinates.bed", "w") as bed_file:
        # Do a for loop which will loop through each gene in the gene_list input and for each, request the required data from the Ensembl API.
        for gene_symbol in gene_list:
            gene_data = get_gene_data(gene_symbol)  # Get gene data from the Ensembl API
            if gene_data:
                # Extract relevant gene info and write it to the BED file
                gene_info = extract_gene_info(gene_data)
                write_to_bed_file(gene_info, bed_file)
    # THIS NEEDS TO BE CHANGED TO LOGGING.
    print("BED file 'genes_coordinates.bed' created successfully.")

# Run the function to create the BED file using the gene list
create_bed_file(gene_list)