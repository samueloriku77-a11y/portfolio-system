import sqlite3
import os

db_path = "sokoyetu.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN business_name VARCHAR")
        c.execute("ALTER TABLE users ADD COLUMN location_address TEXT")
        c.execute("ALTER TABLE users ADD COLUMN location_lat FLOAT")
        c.execute("ALTER TABLE users ADD COLUMN location_lng FLOAT")
        c.execute("ALTER TABLE users ADD COLUMN is_verified_vendor BOOLEAN DEFAULT 0")
        print("Database columns added successfully.")
    except Exception as e:
        print("Error altering table:", e)
    conn.commit()
    conn.close()
else:
    print("Database does not exist yet. Models will generate it on startup.")
