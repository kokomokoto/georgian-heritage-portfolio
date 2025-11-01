"""
Production Database Migration Script for Render.com
Run this on Render.com to fix database schema issues
"""

import os
import sqlite3
from app import app, db

def fix_production_database():
    """Fix database schema issues on production"""
    
    with app.app_context():
        try:
            # Check if we're on PostgreSQL (production) or SQLite (local)
            database_url = os.environ.get('DATABASE_URL')
            
            if database_url and database_url.startswith('postgres'):
                print("Production PostgreSQL detected")
                
                # For PostgreSQL, we need to handle schema migration differently
                # Add media_urls column if it doesn't exist
                try:
                    # Try to add the column (will fail if already exists)
                    db.engine.execute("ALTER TABLE comment ADD COLUMN media_urls TEXT")
                    print("✅ Added media_urls column to PostgreSQL")
                except Exception as e:
                    print(f"Column might already exist: {e}")
                
                # Create all missing tables
                db.create_all()
                print("✅ Ensured all tables exist")
                
            else:
                print("Local SQLite database")
                # Handle SQLite as before
                db.create_all()
                
            print("✅ Database migration completed successfully")
            
        except Exception as e:
            print(f"❌ Database migration failed: {e}")
            raise

if __name__ == '__main__':
    fix_production_database()