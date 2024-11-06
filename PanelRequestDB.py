# Import sqlite3
import sqlite3

def initialize_database():
    # Creating a database connection (this will create `PanelRequests.db` if it doesn't exist)
    conn = sqlite3.connect("PanelRequests.db")

    # Creating a cursor to interact with the database
    cursor = conn.cursor()

    # Creating a table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PanelRequestTable (
            R_code TEXT NOT NULL,
            Test_ID TEXT NOT NULL,
            Clinical_indication TEXT NOT NULL,
            Test_method TEXT NOT NULL,
            Target_genes TEXT NOT NULL,
            Panelapp_genes TEXT NOT NULL
        );
    ''')

    # Commit changes and check tables in the database
    conn.commit()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    # Closing the connection
    conn.close()

# Call the function to initialize the database
initialize_database()