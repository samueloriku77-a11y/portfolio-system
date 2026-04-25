import os
import sys
from urllib.parse import quote_plus
import pymysql

# This script directly tests your Aiven database credentials
# It will confirm 100% if your database is working, so we can isolate Vercel issues.

def test_aiven_connection():
    print("=========================================")
    print("AIVEN MYSQL DATABASE CONNECTION TEST")
    print("=========================================\n")
    
    # User input
    host = "mysql-3e557dfd-samueloriku2004-c3fb.i.aivencloud.com"
    port = "12072"
    user = "avnadmin"
    db_name = "defaultdb"
    
    print(f"Connecting to: {host}:{port}")
    print(f"User: {user}")
    print(f"Database: {db_name}")
    print("\nPaste your Aiven database password (input will be hidden):")
    
    import getpass
    password = getpass.getpass("Password: ")
    
    if not password:
        print("\n❌ Error: Password cannot be empty.")
        return

    # 1. Test raw connection via pymysql
    print("\n--- Test 1: Raw MySQL Connection ---")
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=int(port),
            database=db_name
        )
        
        with connection.cursor() as cursor:
            print(f"✅ Successfully connected to MySQL")
            cursor.execute("select database();")
            record = cursor.fetchone()
            print(f"✅ Connected to database: {record[0]}")
            
            # Check existing tables to see if they collided
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print("\n📋 Existing Tables in Database:")
            for table in tables:
                print(f"  - {table[0]}")
                
        connection.close()
        print("\n✅ Test 1 Passed!")
            
    except Exception as e:
        print(f"\n❌ Test 1 Failed: {e}")
        print("This means your password might be wrong, or your internet is blocking port 12072.")
        return

    # 2. Test SQLAlchemy format (What your apps use)
    print("\n--- Test 2: SQLAlchemy Connection String Format ---")
    encoded_pass = quote_plus(password)
    db_url = f"mysql+pymysql://{user}:{encoded_pass}@{host}:{port}/{db_name}"
    
    print(f"Your Vercel DATABASE_URL should be exactly this:")
    print("-" * 50)
    print(f"{db_url}")
    print("-" * 50)
    print("\n⚠️ COPY THE LINK ABOVE AND PASTE IT INTO VERCEL ENVIRONMENT VARIABLES ⚠️")
    
if __name__ == "__main__":
    try:
        test_aiven_connection()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
