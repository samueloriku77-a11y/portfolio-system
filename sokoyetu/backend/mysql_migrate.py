"""MySQL migration helper to add missing columns to `users` table.

Run with: python mysql_migrate.py
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy import inspect

try:
    from config import DATABASE_TYPE, MYSQL_DB, DATABASE_URL
except Exception:
    # If module path issues occur when running as script
    from .config import DATABASE_TYPE, MYSQL_DB, DATABASE_URL


def ensure_mysql_columns():
    if DATABASE_TYPE != "mysql":
        print("DATABASE_TYPE is not 'mysql' in config. Abort.")
        return

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    cols = {c['name'] for c in inspector.get_columns('users')} if 'users' in inspector.get_table_names() else set()

    to_add = []
    if 'business_name' not in cols:
        to_add.append("ADD COLUMN business_name VARCHAR(255) NULL")
    if 'location_address' not in cols:
        to_add.append("ADD COLUMN location_address TEXT NULL")
    if 'location_lat' not in cols:
        to_add.append("ADD COLUMN location_lat DOUBLE NULL")
    if 'location_lng' not in cols:
        to_add.append("ADD COLUMN location_lng DOUBLE NULL")
    if 'is_verified_vendor' not in cols:
        to_add.append("ADD COLUMN is_verified_vendor BOOLEAN NOT NULL DEFAULT 0")

    if not to_add:
        print("All target columns already exist on `users` table.")
        return

    alter_sql = f"ALTER TABLE users {', '.join(to_add)}"
    print("Applying ALTER TABLE:", alter_sql)
    try:
        with engine.connect() as conn:
            conn.execute(text(alter_sql))
            conn.commit()
        print("✅ Migration applied successfully.")
    except Exception as e:
        print("❌ Failed to apply migration:", e)
    finally:
        engine.dispose()


if __name__ == '__main__':
    ensure_mysql_columns()
