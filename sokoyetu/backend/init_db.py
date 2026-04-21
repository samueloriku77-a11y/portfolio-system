#!/usr/bin/env python
"""
Database initialization script for SokoYetu
Creates MySQL database and tables from models
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from config import DATABASE_TYPE, DATABASE_URL, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB
from models import Base

def create_mysql_database():
    """Create MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server without specifying a database
        mysql_url = f"mysql+pymysql://{MYSQL_USER}"
        if MYSQL_PASSWORD:
            mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        mysql_url += f"@{MYSQL_HOST}:{MYSQL_PORT}"
        
        engine = create_engine(mysql_url)
        with engine.connect() as connection:
            # Create database if it doesn't exist
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}"))
            connection.commit()
            print(f"✅ MySQL database '{MYSQL_DB}' created or already exists")
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Error creating MySQL database: {e}")
        print("\n⚠️  Make sure MySQL is installed and running:")
        print("   Windows: net start MySQL80 (or your MySQL version)")
        print("   Linux/Mac: sudo systemctl start mysql")
        raise

def create_tables():
    """Create all tables from SQLAlchemy models"""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print(f"✅ All tables created in database '{MYSQL_DB}'")
        engine.dispose()
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

def main():
    print(f"🔧 Initializing SokoYetu Database")
    print(f"   Database Type: {DATABASE_TYPE}")
    
    if DATABASE_TYPE == "mysql":
        print(f"   Host: {MYSQL_HOST}:{MYSQL_PORT}")
        print(f"   User: {MYSQL_USER}")
        print(f"   Database: {MYSQL_DB}")
        print()
        
        create_mysql_database()
        create_tables()
        
        print("\n✅ Database initialization complete!")
        print(f"\nYou can now start the backend with:")
        print(f"   python main.py")
        
    else:
        print(f"❌ DATABASE_TYPE is set to '{DATABASE_TYPE}', not 'mysql'")
        print(f"   Update .env file: DATABASE_TYPE=mysql")
        sys.exit(1)

if __name__ == "__main__":
    main()
