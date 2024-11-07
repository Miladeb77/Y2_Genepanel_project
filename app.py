from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to connect to the database and retrieve data
def search_by_patient_or_disorder(search_input):
    with sqlite3.connect("panelapp.db") as panel_conn, sqlite3.connect("dummy_database.db") as patient_conn:
        
        # Check if input is a Patient ID (all numeric)
        if search_input.isdigit():
            patient_cursor = patient_conn.cursor()
            # Query to get all R codes associated with the Patient ID
            patient_cursor.execute("SELECT R_Code FROM patient_data_table WHERE Patient_ID = ?", (search_input,))
            r_codes = [row[0] for row in patient_cursor.fetchall()]

            results = []
            if r_codes:
                panel_cursor = panel_conn.cursor()
                # Query to get panel information associated with each R code
                panel_query = """
                SELECT ?, name AS disease, disease_group, relevant_disorders AS clinical_id,
                       gene_ensembl_id_GRch38, gene_hgnc_symbol, version_created AS version_panelappApi
                FROM panel_info 
                WHERE relevant_disorders IN ({})
                """.format(','.join(['?'] * len(r_codes)))
                
                # Execute the query, passing the patient ID and R codes
                panel_cursor.execute(panel_query, [search_input] + r_codes)
                results = panel_cursor.fetchall()
                
        else:
            # Treat input as an R code and search panel information
            panel_cursor = panel_conn.cursor()
            panel_query = """
            SELECT name AS disease, disease_group, relevant_disorders AS clinical_id,
                   gene_ensembl_id_GRch38, gene_hgnc_symbol, version_created AS version_panelappApi
            FROM panel_info 
            WHERE relevant_disorders = ?
            """
            panel_cursor.execute(panel_query, (search_input,))
            disorder_results = panel_cursor.fetchall()

            # Retrieve associated Patient IDs for this R code
            patient_cursor = patient_conn.cursor()
            patient_cursor.execute("SELECT Patient_ID FROM patient_data_table WHERE R_Code = ?", (search_input,))
            patient_ids = [row[0] for row in patient_cursor.fetchall()]

            # Combine each patient ID with the disorder information
            results = [(pid, *disorder_row) for pid in patient_ids for disorder_row in disorder_results]

    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_input = request.form.get('search_input')
    results = search_by_patient_or_disorder(search_input)

    if results:
        return render_template('results.html', search_input=search_input, results=results)
    else:
        return render_template('results.html', search_input=search_input, results=[], error="No data found for the specified input.")

if __name__ == '__main__':
    app.run(debug=True)
