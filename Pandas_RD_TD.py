import pandas as pd 

import ssl
import certifi

# Set the default SSL context using certifi's certificate bundle
ssl._create_default_https_context = ssl.create_default_context  

# Define function
def load_and_filter_TD ():

    #Load the RD test directory file from website
    url = "https://www.england.nhs.uk/wp-content/uploads/2018/08/national-genomic-test-directory-rare-and-inherited-disease-eligibility-criteria-v7-updated.xlsx"
    df = pd.read_excel(url, sheet_name='R&ID indications', skiprows=[0])

    # Define the list of values to filter in column E
    desired_values = [
        "Medium panel",
        "Small panel",
        "Small panel - deep sequencing",
        "WES",
        "WES or Large Panel",
        "WES or Medium panel",
        "WES or Small Panel",
        "WGS"
    ]

    # Filter rows where column E contains any of the desired values
    filtered_df = df[df['Test Method'].isin(desired_values)]

    return filtered_df

# Give back filtered data
print (load_and_filter_TD())