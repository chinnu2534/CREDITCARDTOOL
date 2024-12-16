import sqlite3

def update_db():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Add 'month' and 'year' columns if not present
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'month' not in columns:
            cursor.execute('''ALTER TABLE transactions ADD COLUMN month INTEGER DEFAULT 1''')
        
        if 'year' not in columns:
            cursor.execute('''ALTER TABLE transactions ADD COLUMN year INTEGER DEFAULT 2024''')

        # Commit changes and close connection
        conn.commit()
        print("Database updated successfully!")
    
    except sqlite3.OperationalError as e:
        print(f"Error updating database: {e}")
    
    finally:
        conn.close()

# Run the function to update the database
update_db()
