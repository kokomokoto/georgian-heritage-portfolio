import sqlite3

conn = sqlite3.connect('instance/portfolio.db')
cursor = conn.cursor()

# Check current columns for comment table
cursor.execute('PRAGMA table_info(comment)')
comment_columns = [col[1] for col in cursor.fetchall()]

# Check current columns for like table
cursor.execute('PRAGMA table_info("like")')
like_columns = [col[1] for col in cursor.fetchall()]

print('Comment table has columns:', comment_columns)
print('Like table has columns:', like_columns)

# Add missing columns to comment table
if 'parent_id' not in comment_columns:
    cursor.execute('ALTER TABLE comment ADD COLUMN parent_id INTEGER')
    print('Added parent_id to comment table')

if 'media_urls' not in comment_columns:
    cursor.execute('ALTER TABLE comment ADD COLUMN media_urls TEXT')
    print('Added media_urls to comment table')

# Add missing columns to like table
if 'project_id' not in like_columns:
    cursor.execute('ALTER TABLE "like" ADD COLUMN project_id TEXT')
    print('Added project_id to like table')

if 'comment_id' not in like_columns:
    cursor.execute('ALTER TABLE "like" ADD COLUMN comment_id INTEGER')
    print('Added comment_id to like table')

conn.commit()
print('Database schema updated successfully')

conn.close()