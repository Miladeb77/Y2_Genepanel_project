import pandas as pd
import ssl
import certifi
import sqlite3

"""
Header:
This script performs the following operations:
1. Downloads an Excel file from a specified URL that contains genomic test data related to rare and inherited diseases.
2. Filters the rows based on specific test methods.
3. Creates an SQLite database (`PanelRequests.db`) and inserts filtered data into a table `PanelRequestTable`.
4. Handles potential duplicates by ignoring them during the insertion into the database.
5. Optionally, prints out the first 5 rows of the database for verification.

Required libraries:
- pandas: for data manipulation and Excel file handling.
- ssl, certifi: for setting up the SSL context when downloading the file.
- sqlite3: for interacting with the SQLite database.

Functions:
- None, the script executes all operations sequentially.

"""

# Set the default SSL context using certifi's certificate bundle
ssl._create_default_https_context = ssl.create_default_context  

# Load the RD test directory file from website into a DataFrame
url = "https://www.england.nhs.uk/wp-content/uploads/2018/08/national-genomic-test-directory-rare-and-inherited-disease-eligibility-criteria-v7-updated.xlsx"
df = pd.read_excel(url, sheet_name='R&ID indications', skiprows=[0])
"""
Reads the Excel file from the provided URL and loads the 'R&ID indications' sheet
into a pandas DataFrame while skipping the first row (usually headers or metadata).
"""

# Define the list of values to filter in column 'Test Method'
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
"""
This list contains the specific test methods that we are interested in.
The rows with any of these values in the 'Test Method' column will be kept.
"""

# Filter rows where column 'Test Method' contains any of the desired values
filtered_df = df[df['Test Method'].isin(desired_values)]
"""
Filters the DataFrame by selecting rows where the 'Test Method' column contains any
of the values listed in 'desired_values'.
"""

# Creating a connection to an SQLite database (creates `PanelRequests.db` if it doesn't exist)
conn = sqlite3.connect("PanelRequests.db")

# Creating a cursor to interact with the database
cursor = conn.cursor()

# Create the table `PanelRequestTable` if it does not already exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS PanelRequestTable (
        Clinical_indication_ID TEXT NOT NULL,
        Test_ID TEXT NOT NULL,
        Clinical_Indication TEXT NOT NULL,
        Test_Method TEXT NOT NULL,
        "Target_Gene" TEXT NOT NULL,
        PRIMARY KEY (Clinical_indication_ID, Test_ID)  -- Ensures no duplicate entries
    );
''')
"""
Creates a table `PanelRequestTable` in the SQLite database with columns:
- Clinical_indication_ID (TEXT): Unique identifier for the clinical indication.
- Test_ID (TEXT): Unique identifier for the test.
- Clinical_Indication (TEXT): Description of the clinical indication.
- Test_Method (TEXT): The method of the test.
- Target_Gene (TEXT): The gene(s) targeted by the test.

A composite primary key is set on `Clinical_indication_ID` and `Test_ID` to avoid duplicate entries.
"""

# Committing changes to the database
conn.commit()

# Insert rows from filtered DataFrame into the `PanelRequestTable`
for index, row in filtered_df.iterrows():
    # Extract values for each column from the current row
    clinical_indication_id = row['Clinical indication ID']
    test_id = row['Test ID']
    clinical_indication = row['Clinical Indication']
    test_method = row['Test Method']
    target_gene = row['Target/Genes']
    
    try:
        # Insert the data into the table, ignoring duplicates
        cursor.execute('''
            INSERT OR IGNORE INTO PanelRequestTable (
                Clinical_indication_ID,
                Test_ID,
                Clinical_Indication,
                Test_Method,
                "Target_Gene"
            ) VALUES (?, ?, ?, ?, ?)
        ''', (clinical_indication_id, test_id, clinical_indication, test_method, target_gene))
    except sqlite3.IntegrityError:
        # If a duplicate entry is encountered, it will be skipped
        print(f"Skipping duplicate entry: {clinical_indication_id}, {test_id}")

"""
The script loops through each row in the filtered DataFrame and attempts to insert it into
the SQLite database. If a duplicate entry is found (based on the primary key), it is skipped.
"""

# Commit the transaction to ensure all data is saved
conn.commit()

# Check if any data has been inserted (optional)
cursor.execute("SELECT * FROM PanelRequestTable LIMIT 5;")
print(cursor.fetchall())
"""
This query selects the first 5 rows from the `PanelRequestTable` to verify that the data
was successfully inserted into the database. The results are printed to the console.
"""

# Closing the connection to the database
conn.close()
"""
Closes the SQLite database connection to ensure that the resources are properly released.
"""

