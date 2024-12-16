import sqlite3

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect('database.db')

# Create a cursor object to execute SQL commands
cur = conn.cursor()

# Create the `cards` table
cur.execute('''
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    card_number TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    outstanding REAL NOT NULL
)
''')

# Create the `transactions` table
cur.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    amount REAL NOT NULL,
    paid INTEGER DEFAULT 0,
    paid_date TEXT,
    FOREIGN KEY (card_id) REFERENCES cards (id)
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database initialized with required tables!")
