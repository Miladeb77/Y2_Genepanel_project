import pytest
import os
from PanelGeneMapper.modules.make_bed_file import (
    create_local_db,
    cache_exon_data,
    fetch_cached_data,
    extract_ensembl_ids_from_csv,
    get_mane_exon_data,
    write_bed_file,
    fetch_all_data,
)

def test_get_mane_exon_data_success():
    """
    This tests that the get_mane_exon_data function returns an expected dictionary 
    output when provided with valid inputs.
    """
    species = "homo_sapiens"  # Species for the API query.
    server = "https://rest.ensembl.org"  # Ensembl API server URL.
    headers = {"Content-Type": "application/json"}  # Headers for the API request.
    ensembl_id = "ENSG00000012048"

    result = get_mane_exon_data(ensembl_id, species, server, headers)
    assert type(result) == dict

def test_get_mane_exon_data_fail():
    """
    This tests that the get_mane_exon_data function returns None when an invalid input is provided
    """
    species = "test"  # Species for the API query.
    server = "https://rest.ensembl.org"  # Ensembl API server URL.
    headers = {"Content-Type": "application/json"}  # Headers for the API request.
    ensembl_id = "ENSG00000012048"

    result = get_mane_exon_data(ensembl_id, species, server, headers)
    assert result == None

def test_extract_ensembl_ids_success():
    """
    This tests that the extract_ensembl_id function returns an expected list 
    output when provided with valid inputs.
    """
    csv_file = "gene_list.csv" 

    result = extract_ensembl_ids_from_csv(csv_file)
    assert type(result) == list

def test_extract_ensembl_ids_fail():
    """
    This tests that the extract_ensembl_ids function returns an error when an invalid input is provided
    """
    csv_file = "gene_list" 

    result = extract_ensembl_ids_from_csv(csv_file)
    assert result == "Error with input CSV"

def test_fetch_all_data_success():
    """
    This tests that the fetch_all_data function returns an expected list 
    output when provided with valid inputs.
    """
    ensembl_gene_ids = ['ENSG00000128973', 'ENSG00000136827', 'ENSG00000064601', 'ENSG00000144381', 'ENSG00000143469']
    species =  "homo_sapiens"
    server = "https://rest.ensembl.org"
    headers = {"Content-Type": "application/json"}

    result = fetch_all_data(ensembl_gene_ids, species, server, headers)
    assert type(result) == list

def test_fetch_all_data_fail():
    '''
    This tests that the fetch_all_data function returns an empty output when an invalid input is provided
    '''
    ensembl_gene_ids = []
    species =  "homo_sapiens"
    server = "https://rest.ensembl.org"
    headers = {"Content-Type": "application/json"}

    result = fetch_all_data(ensembl_gene_ids, species, server, headers)
    assert result == []

def test_write_bed_file_success():
    """
    This tests that the write_bed_file function returns an expected output
    file when provided with valid inputs.
    """
    data_list = ['ENSG00000128973', 'ENSG00000136827', 'ENSG00000064601', 'ENSG00000144381', 'ENSG00000143469']
    output_file = 'gene_exons.bed'
    
    result = write_bed_file(data_list, output_file)
    assert os.path.exists(output_file)
