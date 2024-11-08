import sqlite3

"""
Header:
This script connects to an SQLite database and performs the following operations:

1. Creates a database called `dummy_database.db` (if it does not already exist).
2. Creates a table called `patient_data_table` in the database, if it does not already exist. The table contains three columns:
    - ID (primary key): Integer type.
    - Patient_ID (text): The unique ID for the patient.
    - R_Code (text): The code associated with the patient.
3. Inserts a predefined list of dummy data into the `patient_data_table`.
4. Commits the transaction to the database and closes the connection.

The database and table are used to store sample patient data for testing or further processing.

Required Libraries:
- sqlite3: To interact with SQLite databases.

Functions:
- None. The script executes these steps sequentially.
"""

# Create a connection to an SQLite database (it creates the file if it doesn't exist)
conn = sqlite3.connect("dummy_database.db")

# Create a cursor object that allows interaction with the database
cursor = conn.cursor()

# Create the patient_data_table if it doesn't already exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS patient_data_table (
        ID INTEGER PRIMARY KEY,               
        Patient_ID TEXT NOT NULL,            
        R_Code TEXT NOT NULL,                
        Test_Date DATE NOT NULL               
    );
''')
"""
The SQL script above checks if the `patient_data_table` exists. If it doesn't, it creates the table
with three columns:
- ID: an integer primary key (auto-incremented).
- Patient_ID: a unique identifier for each patient (text type, cannot be NULL).
- R_Code: the code associated with the patient (text type, cannot be NULL).
"""

# Define the dummy data to be inserted into the patient_data_table
data = [
    ('2123689037', 'R210', '2024-11-08'),
    ('9758778104', 'R210', '2024-11-08'),
    ('4075833544', 'R210', '2024-11-08'),
    ('2123689037', 'R207', '2024-11-08'),
    ('7799569397', 'R367', '2024-11-08'),
    ('2123689037', 'R226', '2024-11-08'),
    ('6289973033', 'R223', '2024-11-08'),
    ('1938934295', 'R211', '2024-11-08'),
    ('3925277976', 'R211', '2024-11-08'),
    ('6398739015', 'R347', '2024-11-08'),
    ('2123689037', 'R363', '2024-11-08'),
    ('5600065292', 'R430', '2024-11-08'),
    ('3935563874', 'R224', '2024-11-08'),
    ('3524454924', 'R366', '2024-11-08'),
    ('8003187557', 'R29', '2024-11-08'),
    ('9835827406', 'R377', '2024-11-08'),
    ('4335908331', 'R331', '2024-11-08'),
    ('7523999369', 'R320', '2024-11-08'),
    ('6964999727', 'R157', '2024-11-08'),
    ('3604884492', 'R96', '2024-11-08'),
    ('6720079760', 'R95', '2024-11-08'),
    ('7046896061', 'R50', '2024-11-08'),
    ('6460915874', 'R50', '2024-11-08'),
    ('4505915050', 'R279', '2024-11-08'),
    ('8417342097', 'R268', '2024-11-08'),
    ('311311460', 'R280', '2024-11-08'),
    ('7211305201', 'R280', '2024-11-08'),
    ('9899210736', 'R281', '2024-11-08'),
    ('8067470066', 'R139', '2024-11-08'),
    ('284995886', 'R42', '2024-11-08'),
    ('1271909658', 'R42', '2024-11-08'),
    ('767503608', 'R216', '2024-11-08'),
    ('6500461163', 'R26', '2024-11-08'),
    ('7085575639', 'R98', '2024-11-08'),
    ('7857643609', 'R98', '2024-11-08'),
    ('5807587552', 'R82', '2024-11-08'),
    ('6980783650', 'R388', '2024-11-08'),
    ('5076817972', 'R378', '2024-11-08'),
    ('3697710306', 'R383', '2024-11-08'),
    ('7133292404', 'R409', '2024-11-08'),
    ('7649062358', 'R158', '2024-11-08'),
    ('7655130696', 'R127', '2024-11-08'),
    ('1335681312', 'R210', '2024-11-08'),
    ('1145783244', 'R211', '2024-11-08'),
    ('5760265125', 'R223', '2024-11-08'),
    ('3248028013', 'R226', '2024-11-08'),
    ('7150219106', 'R50', '2024-11-08'),
    ('4737208858', 'R279', '2024-11-08'),
    ('5846471', 'R281', '2024-11-08'),
    ('9448857243', 'R216', '2024-11-08')
]


"""
The data variable is a list of sets of information, where each set contains:

Patient_ID: A unique ID assigned to the patient.
R_Code: R_code associated with patient.
Test_Date: The date when the test was run for patient. 
Each set of information represents a single patient's details.

This data will be inserted into the `patient_data_table` in the SQLite database.
"""

# Insert each row of data into the patient_data_table
cursor.executemany('''
    INSERT INTO patient_data_table (Patient_ID, R_Code, Test_Date) VALUES (?, ?, ?)
''', data)

"""
The `executemany` function is used to insert multiple rows of data into the table at once. It helps improve
performance when inserting large amounts of data.
Each row from the `data` list is inserted into the `patient_data_table` with the values for Patient_ID and R_Code.
"""

# Commit the transaction to save the changes to the database
conn.commit()
"""
The `commit()` function ensures that all changes made during the session (inserting the data) are saved
to the database. Without this step, the changes will not be persistent.
"""

# Close the connection to the SQLite database
conn.close()
"""
Finally, the `close()` method is called to close the connection to the SQLite database, releasing any
resources that were being used.
"""
