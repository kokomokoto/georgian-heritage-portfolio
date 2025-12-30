#!/usr/bin/env python3
"""
Test script to verify new database connection and data migration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_new_database():
    """Test the new database connection and data"""

    new_db_url = os.environ.get('DATABASE_URL')
    if not new_db_url:
        print("❌ DATABASE_URL not set in .env file")
        return

    print("🔍 Testing database connection...")
    print(f"   URL: {new_db_url[:50]}...")

    from app import app, db, Project, Comment, User, Like

    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = new_db_url

        with app.app_context():
            # Test connection using modern SQLAlchemy
            with db.engine.connect() as connection:
                result = connection.execute(db.text('SELECT 1'))
                print("✅ Database connection successful")

            # Check data counts
            project_count = Project.query.count()
            comment_count = Comment.query.count()
            user_count = User.query.count()
            like_count = Like.query.count()

            print("📊 Data in database:")
            print(f"   Projects: {project_count}")
            print(f"   Comments: {comment_count}")
            print(f"   Users: {user_count}")
            print(f"   Likes: {like_count}")

            if project_count > 0:
                print("✅ Database contains data!")
                # Show sample project
                sample_project = Project.query.first()
                print(f"📋 Sample project: {sample_project.title}")
            else:
                print("⚠️ No projects found - database might be empty")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print("   This might be expected if using old database URL")
        print("   Update DATABASE_URL in .env to test new database")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_database()