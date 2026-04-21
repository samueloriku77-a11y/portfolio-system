import sqlite3

conn = sqlite3.connect('sokoyetu.db')
cursor = conn.cursor()

# Get users table schema
cursor.execute('PRAGMA table_info(users)')
print('Users table schema:')
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]} {'NULL' if col[3] else 'NOT NULL'} {'DEFAULT ' + str(col[4]) if col[4] is not None else ''}")

conn.close()