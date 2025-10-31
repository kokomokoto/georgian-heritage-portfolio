#!/usr/bin/env python3
"""
Migration script to import comments from comments.json to SQLite database
კომენტარების მიგრაცია comments.json-დან SQLite მონაცემთა ბაზაში
"""

import json
import os
from datetime import datetime
from app import app, db
from models import User, Comment

def import_comments_from_json():
    """Import comments from comments.json to database"""
    
    # Check if comments.json exists
    if not os.path.exists('comments.json'):
        print("❌ comments.json not found!")
        return
        
    print("📥 Loading comments from comments.json...")
    
    with open('comments.json', 'r', encoding='utf-8') as f:
        json_comments = json.load(f)
    
    with app.app_context():
        # Create a default user for imported comments if needed
        default_user = User.query.filter_by(email='imported@comments.local').first()
        if not default_user:
            default_user = User(
                name='Imported User',
                email='imported@comments.local',
                email_verified=True
            )
            default_user.set_password('imported123')
            db.session.add(default_user)
            db.session.commit()
            print(f"✅ Created default user: {default_user.email}")
        
        total_imported = 0
        
        # Process each project's comments
        for project_id, comments_list in json_comments.items():
            print(f"\n📂 Processing project: {project_id}")
            
            for comment_data in comments_list:
                # Import main comment
                main_comment = Comment(
                    content=comment_data.get('text', ''),
                    project_id=project_id,
                    user_id=default_user.id,
                    parent_id=None
                )
                
                # Handle media - convert single media to JSON array format
                if comment_data.get('media'):
                    # Convert old media format to new format
                    media_url = comment_data['media']
                    if not media_url.startswith('http'):
                        # Local file path - convert to project path
                        media_url = f"/projects/{project_id}/comments/{media_url}"
                    main_comment.set_media_urls([media_url])
                
                db.session.add(main_comment)
                db.session.flush()  # Get the ID
                total_imported += 1
                
                print(f"  ✅ Imported comment: {comment_data.get('text', '')[:50]}...")
                
                # Import replies
                for reply_data in comment_data.get('replies', []):
                    reply_comment = Comment(
                        content=reply_data.get('text', ''),
                        project_id=project_id,
                        user_id=default_user.id,
                        parent_id=main_comment.id
                    )
                    
                    # Handle reply media
                    if reply_data.get('media'):
                        media_url = reply_data['media']
                        if not media_url.startswith('http'):
                            media_url = f"/projects/{project_id}/comments/{media_url}"
                        reply_comment.set_media_urls([media_url])
                    
                    db.session.add(reply_comment)
                    total_imported += 1
                    
                    print(f"    ↳ Reply: {reply_data.get('text', '')[:30]}...")
        
        # Commit all changes
        db.session.commit()
        print(f"\n🎉 Successfully imported {total_imported} comments from JSON!")
        
        # Verify the import
        total_in_db = Comment.query.count()
        print(f"📊 Total comments now in database: {total_in_db}")

if __name__ == '__main__':
    print("🚀 Starting comments migration from JSON to SQLite...")
    import_comments_from_json()
    print("✅ Migration completed!")