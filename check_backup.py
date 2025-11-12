import sqlite3

conn = sqlite3.connect('portfolio_backup.db')
cursor = conn.cursor()

# Check if project table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project'")
if cursor.fetchone():
    cursor.execute('SELECT COUNT(*) FROM project')
    count = cursor.fetchone()[0]
    print('Projects in backup DB:', count)

    cursor.execute('SELECT title FROM project')
    titles = cursor.fetchall()
    print('Project titles:')
    for title in titles:
        print(' -', title[0])
else:
    print('No project table in backup database')

conn.close()