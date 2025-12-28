#!/usr/bin/env python3
"""
Migration script to move comments from JSON file to database
"""
import os
import json
import sys
from flask import Flask
from models import db, Comment, User

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def migrate_comments_to_db():
    """Migrate comments from comments.json to database"""

    # Initialize Flask app
    app = Flask(__name__)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)

    with app.app_context():
        # Check if comments already exist in database
        existing_comments = Comment.query.all()
        if existing_comments:
            print(f"⚠️  Database already has {len(existing_comments)} comments.")
            return

        # Load comments from JSON
        comments_json = 'comments.json'
        if not os.path.exists(comments_json):
            print("❌ comments.json not found!")
            return

        with open(comments_json, 'r', encoding='utf-8') as f:
            comments_by_project = json.load(f)

        print(f"📁 Found comments for {len(comments_by_project)} projects in JSON file")

        # Get or create a default user for comments
        # Since comments might not have user info, we'll create a default user
        default_user = User.query.filter_by(email='anonymous@example.com').first()
        if not default_user:
            default_user = User(
                name='Anonymous',
                email='anonymous@example.com',
                password_hash='dummy',  # This won't be used
                email_verified=True,
                is_admin=False
            )
            db.session.add(default_user)
            db.session.commit()
            print("✅ Created default anonymous user")

        total_comments = 0

        # Migrate comments for each project
        for project_id, comments_list in comments_by_project.items():
            print(f"Processing {len(comments_list)} comments for project {project_id}")
            
            for comment_data in comments_list:
                # Create main comment
                media_urls = []
                if comment_data.get('media'):
                    media_urls = [comment_data['media']]
                
                main_comment = Comment(
                    content=comment_data.get('text', ''),
                    project_id=project_id,
                    user_id=default_user.id,
                    media_urls=json.dumps(media_urls) if media_urls else None
                )
                
                db.session.add(main_comment)
                db.session.flush()  # Get the ID
                
                total_comments += 1
                
                # Process replies
                for reply_data in comment_data.get('replies', []):
                    reply_media_urls = []
                    if reply_data.get('media'):
                        reply_media_urls = [reply_data['media']]
                    
                    reply_comment = Comment(
                        content=reply_data.get('text', ''),
                        project_id=project_id,
                        user_id=default_user.id,
                        parent_id=main_comment.id,
                        media_urls=json.dumps(reply_media_urls) if reply_media_urls else None
                    )
                    
                    db.session.add(reply_comment)
                    total_comments += 1

        # Commit all changes
        db.session.commit()
        print(f"🎉 Successfully migrated {total_comments} comments to database!")

if __name__ == '__main__':
    migrate_comments_to_db()