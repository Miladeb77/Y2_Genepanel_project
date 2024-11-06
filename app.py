from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

# Route for the main page with input form
@app.route('/')
def index():
    return '''
    <h2>Enter Relevant Disorder Code (e.g., R160)</h2>
    <form action="/search" method="post">
        <input type="text" name="relevant_disorder" placeholder="Enter code" required>
        <button type="submit">Search</button>
    </form>
    '''

# Route to handle search and display results
@app.route('/search', methods=['POST'])
def search():
    relevant_disorder = request.form['relevant_disorder']
    
    # Connect to the database and set row factory
    conn = sqlite3.connect('panelapp.db')
    conn.row_factory = sqlite3.Row  # This makes rows behave like dictionaries
    cursor = conn.cursor()

    # Execute SQL query to get all rows where relevant_disorders matches the input
    cursor.execute("SELECT * FROM panel_info WHERE relevant_disorders = ?", (relevant_disorder,))
    rows = cursor.fetchall()
    conn.close()

    # Pass rows to the template for rendering
    return render_template('results.html', rows=rows, disorder=relevant_disorder)

if __name__ == '__main__':
    app.run(debug=True)
