import sqlite3
import os

DB_PATH = "sokoyetu.db"

def promote():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Let's promote the primary test accounts to ensure access
    emails = ['customer1@test.com', 'admin@test.com']
    
    for email in emails:
        cur.execute("UPDATE users SET role='ADMIN' WHERE email=?", (email,))
        print(f"Updated {email} to ADMIN role.")
    
    conn.commit()
    conn.close()
    print("Promotion complete.")

if __name__ == "__main__":
    promote()
