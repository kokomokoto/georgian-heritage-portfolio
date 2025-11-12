import sqlite3

conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(project)')
columns = cursor.fetchall()
print('Columns:', [col[1] for col in columns])

cursor.execute('SELECT sql FROM sqlite_master WHERE name="project"')
create_sql = cursor.fetchone()
print('Create SQL:', create_sql[0] if create_sql else 'None')

conn.close()