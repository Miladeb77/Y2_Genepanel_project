import pandas as pd
import ssl
import certifi
import sqlite3

# Set the default SSL context using certifi's certificate bundle
ssl._create_default_https_context = ssl.create_default_context  

# Load the RD test directory file from website
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

# Creating a database connection (this will create `PanelRequests.db` if it doesn't exist)
conn = sqlite3.connect("PanelRequests.db")

# Creating a cursor to interact with the database
cursor = conn.cursor()

# Creating a table with "Target/Gene" as the column name if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS PanelRequestTable (
        Clinical_indication_ID TEXT NOT NULL,
        Test_ID TEXT NOT NULL,
        Clinical_Indication TEXT NOT NULL,
        Test_Method TEXT NOT NULL,
        "Target_Gene" TEXT NOT NULL,
        PRIMARY KEY (Clinical_indication_ID, Test_ID)  -- Ensuring no duplicate entries
    );
''')

# Committing changes and checking tables in the database
conn.commit()

# Insert rows from filtered DataFrame into the PanelRequestTable
for index, row in filtered_df.iterrows():
    # Extract values for each column
    clinical_indication_id = row['Clinical indication ID']
    test_id = row['Test ID']
    clinical_indication = row['Clinical Indication']
    test_method = row['Test Method']
    target_gene = row['Target/Genes']
    
    try:
        # Try to insert the new data, ignoring duplicate entries
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
        # If any data violates the integrity constraints, skip it
        print(f"Skipping duplicate entry: {clinical_indication_id}, {test_id}")

# Commit the transaction
conn.commit()

# Check if data has been inserted (optional)
cursor.execute("SELECT * FROM PanelRequestTable LIMIT 5;")
print(cursor.fetchall())

# Closing the connection
conn.close()