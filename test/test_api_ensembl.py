from ensembl_package.api_ensembl import *

def test_get_mane_exon_data_success():
    species = "homo_sapiens"  # Species for the API query.
    server = "https://rest.ensembl.org"  # Ensembl API server URL.
    headers = {"Content-Type": "application/json"}  # Headers for the API request.
    ensembl_id = "ENSG00000012048"

    result = get_mane_exon_data(ensembl_id, species, server, headers)
    assert type(result) == dict


def test_get_mane_exon_data_fail():
    species = "test"  # Species for the API query.
    server = "https://rest.ensembl.org"  # Ensembl API server URL.
    headers = {"Content-Type": "application/json"}  # Headers for the API request.
    ensembl_id = "ENSG00000012048"

    result = get_mane_exon_data(ensembl_id, species, server, headers)
    assert result == None


def test_extract_ensembl_ids_success():
    csv_file = "gene_list.csv" 

    result = extract_ensembl_ids(csv_file)
    assert type(result) == list


def test_extract_ensembl_ids_fail():
    csv_file = "gene_list" 

    result = extract_ensembl_ids(csv_file)
    assert result == "Error with input CSV"
