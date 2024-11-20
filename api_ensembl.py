# import modules required for this script to run
import requests
import json
 
# Define the server URL needed to connect to Ensembl REST API.
server = "https://rest.ensembl.org"
 
# Define the species of the genome we need. This is needed to get the correct genome from Ensembl.
species = "homo_sapiens"
 
# Define a list of genes for testing purposes. this represents the user input which will be a list of genes for a specific R Code.
gene_list = ["BRCA2", "TP53", "EGFR"]
 
# Define the headers for the API request. The API request response needs to be in JSON format.
headers = {"Content-Type": "application/json"}
 
# Create a BED file which will be the final output
# Open a new BED file named genomics_coordinates.bed. this has write permissions.
with open("genes_coordinates.bed", "w") as bed_file:
    # Do a for loop which will loop through each gene in the gene_list input and for each, request the required data from the Ensembl API.
    for gene_symbol in gene_list:
        # Define the endpoint. We need to look up the data in the Ensembl API using the gene symbol (gene name).
        gene_endpoint = f"/lookup/symbol/{species}/{gene_symbol}"
 
        # This is the full URL for the location in the Ensembl API where we request the required data for each gene.
        gene_url = f"{server}{gene_endpoint}"
 
        # Do the API request.
        gene_response = requests.get(gene_url, headers=headers)

        #  If we have successfully connected to the Ensembl API, start retrieving required data and writing to BED file.
        if gene_response.ok:
            # Create a python variable for the output of the API request (which is in JSON format) so that it can be used downstream.
            gene_data = gene_response.json()
 
            # Retrieve the relevant data from Ensembl API and put each into its own variable.
            chrom = gene_data.get("seq_region_name")  # Chromosome
            gene_start = gene_data.get("start")      # Gene start position
            gene_end = gene_data.get("end")          # Gene end position
            gene_name = gene_data.get("display_name")  # Gene name
 
            # Write the retrieved data to the BED file (chrom, start, end, gene name)
            bed_file.write(f"{chrom}\t{gene_start}\t{gene_end}\t{gene_name}\n")
       # If data was not retrieved correctly print an error. THIS NEEDS TO BE CHANGED TO LOGGING.
       else:
            print(f"Error fetching data for gene {gene_symbol}: {gene_response.status_code} - {gene_response.reason}")
 # THIS NEEDS TO BE CHANGED TO LOGGING.
print("BED file 'genes_coordinates.bed' created successfully.")