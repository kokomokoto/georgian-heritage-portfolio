#!/usr/bin/env python3
from app import app, db
import sqlite3

with app.app_context():
    print('Creating all database tables...')
    db.create_all()
    print('Database tables created successfully!')
    
    # Check what tables exist now
    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('Tables in database:')
    for table in tables:
        print(f'  {table[0]}')
    
    # Check comment table structure
    if any(table[0] == 'comment' for table in tables):
        cursor.execute('PRAGMA table_info(comment);')
        columns = cursor.fetchall()
        print('Comment table columns:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
    
    conn.close()