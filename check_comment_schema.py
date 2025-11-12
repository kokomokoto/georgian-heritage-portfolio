import sqlite3

conn = sqlite3.connect('instance/portfolio.db')
cursor = conn.cursor()

print('Comment table columns:')
cursor.execute('PRAGMA table_info(comment)')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[1]}: {col[2]}')

print('\nLike table columns:')
cursor.execute('PRAGMA table_info("like")')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[1]}: {col[2]}')

conn.close()