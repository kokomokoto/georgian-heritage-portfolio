#!/usr/bin/env python3
"""
Database migration script to update Comment model from single media_url to multiple media_urls
"""

import sqlite3
import json
import os
from app import app, db
from models import Comment

def migrate_database():
    """Migrate database schema from media_url to media_urls"""
    
    # Get database path from app config
    db_path = 'site.db'  # Default SQLite database
    
    print(f"Migrating database: {db_path}")
    
    # Create connection to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if old media_url column exists
        cursor.execute("PRAGMA table_info(comment)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in comment table: {columns}")
        
        if 'media_url' in columns and 'media_urls' not in columns:
            print("Migration needed: media_url -> media_urls")
            
            # Get all comments with media_url
            cursor.execute("SELECT id, media_url FROM comment WHERE media_url IS NOT NULL AND media_url != ''")
            comments_with_media = cursor.fetchall()
            print(f"Found {len(comments_with_media)} comments with media")
            
            # Add new media_urls column
            cursor.execute("ALTER TABLE comment ADD COLUMN media_urls TEXT")
            print("Added media_urls column")
            
            # Migrate data from media_url to media_urls (as JSON array)
            for comment_id, media_url in comments_with_media:
                # Convert single URL to JSON array
                media_urls_json = json.dumps([media_url])
                cursor.execute("UPDATE comment SET media_urls = ? WHERE id = ?", 
                             (media_urls_json, comment_id))
                print(f"Migrated comment {comment_id}: {media_url} -> {media_urls_json}")
            
            # Remove old media_url column by recreating table
            print("Recreating table without media_url column...")
            
            # Create new table structure
            cursor.execute("""
                CREATE TABLE comment_new (
                    id INTEGER PRIMARY KEY,
                    content TEXT NOT NULL,
                    project_id VARCHAR(50) NOT NULL,
                    user_id INTEGER NOT NULL,
                    parent_id INTEGER,
                    media_urls TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (parent_id) REFERENCES comment(id)
                )
            """)
            
            # Copy data to new table
            cursor.execute("""
                INSERT INTO comment_new (id, content, project_id, user_id, parent_id, media_urls, created_at)
                SELECT id, content, project_id, user_id, parent_id, media_urls, created_at 
                FROM comment
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE comment")
            cursor.execute("ALTER TABLE comment_new RENAME TO comment")
            
            print("Successfully migrated database schema!")
            
        elif 'media_urls' in columns:
            print("Migration already completed - media_urls column exists")
            
        else:
            print("No migration needed - fresh database")
            
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starting database migration...")
    migrate_database()
    print("Migration process finished.")
        
        # Check if media_urls column exists
        has_media_urls = any(col[1] == 'media_urls' for col in columns)
        has_media_url = any(col[1] == 'media_url' for col in columns)
        
        print(f'Has media_urls column: {has_media_urls}')
        print(f'Has media_url column: {has_media_url}')
        
        if not has_media_urls:
            print('Adding media_urls column...')
            cursor.execute('ALTER TABLE comment ADD COLUMN media_urls TEXT;')
            conn.commit()
            print('Column added successfully!')
        
        # Now migrate data if both columns exist
        if has_media_url:
            print('Migrating data from media_url to media_urls...')
            cursor.execute('SELECT id, media_url FROM comment WHERE media_url IS NOT NULL AND media_url != ""')
            comments_with_media = cursor.fetchall()
            
            migrated = 0
            for comment_id, media_url in comments_with_media:
                # Convert single URL to JSON array
                media_urls_json = json.dumps([media_url])
                cursor.execute('UPDATE comment SET media_urls = ? WHERE id = ?', (media_urls_json, comment_id))
                migrated += 1
                print(f'Migrated comment {comment_id}: {media_url} -> {media_urls_json}')
            
            conn.commit()
            print(f'Migration completed: {migrated} comments updated')
        
        conn.close()
        print('Database migration finished!')

if __name__ == '__main__':
    migrate_database()