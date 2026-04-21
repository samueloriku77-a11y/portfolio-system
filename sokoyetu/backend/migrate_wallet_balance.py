import sqlite3

def add_wallet_balance_column():
    """Add the wallet_balance column to the users table"""
    conn = sqlite3.connect('sokoyetu.db')
    cursor = conn.cursor()

    try:
        # Add wallet_balance column with default value of 0.0
        cursor.execute('ALTER TABLE users ADD COLUMN wallet_balance REAL DEFAULT 0.0')
        conn.commit()
        print("✅ Successfully added wallet_balance column to users table")

        # Verify the column was added
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        wallet_balance_found = any(col[1] == 'wallet_balance' for col in columns)

        if wallet_balance_found:
            print("✅ Verification: wallet_balance column exists")
        else:
            print("❌ Error: wallet_balance column was not added")

    except sqlite3.Error as e:
        print(f"❌ Error adding wallet_balance column: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_wallet_balance_column()