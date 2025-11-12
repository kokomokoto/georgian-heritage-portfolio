import sqlite3

conn = sqlite3.connect('projects.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)

if tables:
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"Columns in {table[0]}:", [col[1] for col in columns])

conn.close()