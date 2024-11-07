#import all of the moduled needed for the function. SQLite is needed to run SQL to generate a SQL table
import sqlite3

#create a database to contain the dummy data. Connect this python script to the sql database so that it is able to interact with it. 
conn = sqlite3.connect("dummy_database.db")

#create a temporary object which allows this script to execute sql commands
cursor = conn.cursor()

#first execute the sql script that will create a table. Then create the table if a table with the exact same name does not already exist.

cursor.execute('''
    CREATE TABLE IF NOT EXISTS patient_data_table (
        ID INTEGER PRIMARY KEY,
        Patient_ID TEXT NOT NULL,
        R_Code TEXT NOT NULL
    );
''')

#assign the list of data to be inserted into the patient_data_table to the data variable 
data = [
    ('2123689037', 'R210'),
    ('9758778104', 'R210'),
    ('4075833544', 'R210'),
    ('1902402976', 'R207'),
    ('7799569397', 'R367'),
    ('6248785886', 'R226'),
    ('6289973033', 'R223'),
    ('1938934295', 'R211'),
    ('3925277976', 'R211'),
    ('6398739015', 'R347'),
    ('4031166220', 'R363'),
    ('5600065292', 'R430'),
    ('3935563874', 'R224'),
    ('3524454924', 'R366'),
    ('8003187557', 'R29'),
    ('9835827406', 'R377'),
    ('4335908331', 'R331'),
    ('7523999369', 'R320'),
    ('6964999727', 'R157'),
    ('3604884492', 'R96'),
    ('6720079760', 'R95'),
    ('7046896061', 'R50'),
    ('6460915874', 'R50'),
    ('4505915050', 'R279'),
    ('8417342097', 'R268'),
    ('311311460', 'R280'),
    ('7211305201', 'R280'),
    ('9899210736', 'R281'),
    ('8067470066', 'R139'),
    ('284995886', 'R42'),
    ('1271909658', 'R42'),
    ('767503608', 'R216'),
    ('6500461163', 'R26'),
    ('7085575639', 'R98'),
    ('7857643609', 'R98'),
    ('5807587552', 'R82'),
    ('6980783650', 'R388'),
    ('5076817972', 'R378'),
    ('3697710306', 'R383'),
    ('7133292404', 'R409'),
    ('7649062358', 'R158'),
    ('7655130696', 'R127'),
    ('1335681312', 'R210'),
    ('1145783244', 'R211'),
    ('5760265125', 'R223'),
    ('3248028013', 'R226'),
    ('7150219106', 'R50'),
    ('4737208858', 'R279'),
    ('5846471', 'R281'),
    ('9448857243', 'R216')
]

# Insert each row of data into the patient_data_table
cursor.executemany('''
    INSERT INTO patient_data_table (Patient_ID, R_Code)
    VALUES (?,?,?)
''', data)

# Commit the transaction to save the changes to the patient_data_table
conn.commit()

#close the connection to SQlite
conn.close()