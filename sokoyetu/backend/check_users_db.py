import sqlite3

conn = sqlite3.connect('sokoyetu.db')
cursor = conn.cursor()

# Get user count
cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
print(f'Total users: {count}')

# Get sample users
cursor.execute('SELECT email, role FROM users LIMIT 5')
users = cursor.fetchall()
print('Sample users:')
for user in users:
    print(f'  {user[0]} - {user[1]}')

conn.close()