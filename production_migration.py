#!/usr/bin/env python3
"""
Production-safe database migration script for Render.com
This script safely migrates from media_url to media_urls without breaking existing data
"""

import os
import sqlite3
import json
from app import app, db

def safe_production_migration():
    """Safely migrate database schema in production"""
    
    with app.app_context():
        # Check if we're in production (Render.com)
        is_production = bool(os.environ.get('DATABASE_URL'))
        
        if is_production:
            print("🚀 Running production migration on Render.com...")
            
            # For production PostgreSQL, we need to handle this differently
            database_url = os.environ.get('DATABASE_URL')
            if database_url.startswith('postgres://'):
                # PostgreSQL migration
                print("📊 Migrating PostgreSQL database...")
                migrate_postgresql()
            else:
                print("📊 Unknown database type, skipping migration")
        else:
            print("🏠 Local development - no migration needed")

def migrate_postgresql():
    """Migrate PostgreSQL database safely"""
    try:
        # Import SQLAlchemy for PostgreSQL operations
        from sqlalchemy import text
        
        with db.engine.connect() as conn:
            # Check if media_urls column exists
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='comment' AND column_name='media_urls'
            """))
            
            if result.fetchone() is None:
                print("Adding media_urls column...")
                
                # Add media_urls column
                conn.execute(text("ALTER TABLE comment ADD COLUMN media_urls TEXT"))
                
                # Migrate existing media_url data to media_urls (as JSON array)
                conn.execute(text("""
                    UPDATE comment 
                    SET media_urls = CASE 
                        WHEN media_url IS NOT NULL AND media_url != '' 
                        THEN '["' || media_url || '"]'
                        ELSE NULL 
                    END
                """))
                
                # In a separate migration, we could remove media_url column
                # For now, keep it for safety
                
                conn.commit()
                print("✅ PostgreSQL migration completed successfully!")
            else:
                print("✅ Database already migrated")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    safe_production_migration()