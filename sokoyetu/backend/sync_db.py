import sqlite3
import os

DB_PATH = "sokoyetu.db"

def sync():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columns to add to 'orders' table
    new_columns = [
        ("admin_id", "INTEGER"),
        ("admin_approved_at", "DATETIME"),
        ("admin_notes", "TEXT")
    ]

    print("Checking for missing columns in 'orders' table...")
    
    # Get current columns
    cursor.execute("PRAGMA table_info(orders)")
    columns = [row[1] for row in cursor.fetchall()]

    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column '{col_name}' to 'orders' table...")
            try:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
                print(f"Column '{col_name}' added successfully.")
            except Exception as e:
                print(f"Error adding column '{col_name}': {e}")
        else:
            print(f"Column '{col_name}' already exists.")

    conn.commit()
    conn.close()
    print("Database sync complete.")

if __name__ == "__main__":
    sync()
