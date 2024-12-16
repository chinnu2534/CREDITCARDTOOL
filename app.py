from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route to add a new card and bill together
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        card_name = request.form.get('card_name')
        bill_amount = float(request.form.get('bill_amount', 0))
        bill_month = int(request.form.get('bill_month'))
        bill_year = int(request.form.get('bill_year'))
        paid = 'paid' in request.form  # Check if 'Paid' checkbox is checked
        paid_amount = float(request.form.get('paid_amount', 0)) if paid else 0
        balance = bill_amount - paid_amount

        # Insert card and initial bill details into the database
        conn = get_db_connection()
        
        # Add the card
        conn.execute('''INSERT INTO cards (name) VALUES (?)''', (card_name,))
        
        # Get the newly added card ID
        card_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Add the first bill associated with the card
        conn.execute('''
            INSERT INTO transactions (card_id, month, year, amount, paid, paid_amount, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (card_id, bill_month, bill_year, bill_amount, 0, paid_amount, balance))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))  # Redirect to the dashboard after adding the card and bill

    return render_template('add_card.html')  # Render the form for GET requests




# Route to display dashboard and list of cards
from flask import request, jsonify, render_template

from flask import request, jsonify, render_template

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()

    # Get distinct years from the transactions table
    years_query = '''
        SELECT DISTINCT year
        FROM transactions
        ORDER BY year DESC
    '''
    years = conn.execute(years_query).fetchall()
    years = [year['year'] for year in years]  # Extract the years from the result

    # Get selected month and year from the form
    selected_month = request.form.get('month') if request.method == 'POST' else None
    selected_year = request.form.get('year') if request.method == 'POST' else None

    # Fetch cards based on selected month and year
    if selected_month and selected_year:
        query = '''
            SELECT c.id, c.name, 
                   SUM(t.balance) AS outstanding_balance,
                   SUM(t.amount) AS total_bill_amount
            FROM cards c
            LEFT JOIN transactions t ON c.id = t.card_id
            WHERE t.month = ? AND t.year = ?
            GROUP BY c.id, c.name
        '''
        cards = conn.execute(query, (selected_month, selected_year)).fetchall()
    else:
        # Fetch all cards if no filters are selected
        query = '''
            SELECT c.id, c.name, 
                   SUM(t.balance) AS outstanding_balance,
                   SUM(t.amount) AS total_bill_amount
            FROM cards c
            LEFT JOIN transactions t ON c.id = t.card_id
            GROUP BY c.id, c.name
        '''
        cards = conn.execute(query).fetchall()

    conn.close()

    # Check if the request is AJAX by checking the X-Requested-With header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(cards=[{
            'name': card['name'],
            'total_bill_amount': card['total_bill_amount'],
            'outstanding_balance': card['outstanding_balance'],
            'id': card['id']
        } for card in cards])

    # Otherwise, render the full page
    return render_template('index.html', cards=cards, selected_month=selected_month, selected_year=selected_year, years=years)




@app.route('/card/<int:card_id>/update_paid', methods=['GET', 'POST'])
def update_paid(card_id):
    conn = get_db_connection()
    
    # Fetch the outstanding balance for the card
    card = conn.execute('SELECT * FROM cards WHERE id = ?', (card_id,)).fetchone()
    
    # Fetch the transactions associated with this card
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE card_id = ? ORDER BY year DESC, month DESC',
        (card_id,)
    ).fetchall()

    if request.method == 'POST':
        # Get the paid amount from the form
        paid_amount = float(request.form['paid_amount'])
        transaction_id = request.form['transaction_id']
        
        # Find the transaction to update based on its ID
        transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
        
        if transaction:
            new_balance = transaction['amount'] - paid_amount
            paid = 1 if new_balance <= 0 else 0
            paid_date = None
            if paid:
                paid_date = request.form['paid_date']  # Optional: record the payment date if paid

            # Update the transaction with the new paid amount
            conn.execute('''
                UPDATE transactions
                SET paid_amount = ?, balance = ?, paid = ?, paid_date = ?
                WHERE id = ?
            ''', (paid_amount, new_balance, paid, paid_date, transaction_id))
            
            conn.commit()

        return redirect(url_for('index'))  # Redirect back to the dashboard after update

    return render_template('update_paid.html', card=card, transactions=transactions)




@app.route('/card/<int:card_id>/delete', methods=['POST'])
def delete_card(card_id):
    conn = get_db_connection()
    # First, delete any transactions associated with the card
    conn.execute('DELETE FROM transactions WHERE card_id = ?', (card_id,))
    # Now, delete the card
    conn.execute('DELETE FROM cards WHERE id = ?', (card_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))  # Redirect to the homepage after deleting the card







# Initialize the database with the required tables
def init_db():
    try:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                bill_amount REAL NOT NULL,
                bill_month INTEGER NOT NULL,
                bill_year INTEGER NOT NULL,
                paid INTEGER DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                balance REAL NOT NULL,
                FOREIGN KEY (card_id) REFERENCES cards (id)
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error setting up database:", e)

# Setup the database when the application starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
