#!/usr/bin/env python3
"""
Database Backup and Restore Tool
მონაცემთა ბაზის Backup და აღდგენის ინსტრუმენტი
"""

import os
import json
from datetime import datetime
from app import app, db
from models import User, Comment, Like

def backup_database():
    """Create a JSON backup of all database data"""
    with app.app_context():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'database_backup_{timestamp}.json'
        
        # Collect all data
        backup_data = {
            'timestamp': timestamp,
            'users': [],
            'comments': [],
            'likes': []
        }
        
        # Users
        users = User.query.all()
        for user in users:
            backup_data['users'].append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'password_hash': user.password_hash,
                'email_verified': user.email_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        # Comments
        comments = Comment.query.all()
        for comment in comments:
            backup_data['comments'].append({
                'id': comment.id,
                'content': comment.content,
                'project_id': comment.project_id,
                'user_id': comment.user_id,
                'parent_id': comment.parent_id,
                'media_url': comment.media_url,
                'created_at': comment.created_at.isoformat() if comment.created_at else None
            })
        
        # Likes
        likes = Like.query.all()
        for like in likes:
            backup_data['likes'].append({
                'id': like.id,
                'user_id': like.user_id,
                'comment_id': like.comment_id,
                'created_at': like.created_at.isoformat() if like.created_at else None
            })
        
        # Save backup
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Backup შექმნილია: {backup_filename}")
        print(f"👥 მომხმარებლები: {len(backup_data['users'])}")
        print(f"💬 კომენტარები: {len(backup_data['comments'])}")
        print(f"👍 ლაიქები: {len(backup_data['likes'])}")
        
        return backup_filename

def restore_database(backup_filename):
    """Restore database from JSON backup"""
    with app.app_context():
        if not os.path.exists(backup_filename):
            print(f"❌ Backup ფაილი ვერ მოიძებნა: {backup_filename}")
            return False
        
        with open(backup_filename, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        print(f"🔄 Database აღდგენა {backup_filename}-დან...")
        
        # Clear existing data (CAREFUL!)
        print("⚠️ WARNING: ამოიშლება არსებული მონაცემები!")
        confirm = input("გნებავთ გაგრძელება? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ აღდგენა გაუქმდა")
            return False
        
        # Delete existing records
        Like.query.delete()
        Comment.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Restore users
        for user_data in backup_data['users']:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                email_verified=user_data['email_verified']
            )
            user.password_hash = user_data['password_hash']  # Direct assignment
            if user_data['created_at']:
                user.created_at = datetime.fromisoformat(user_data['created_at'])
            db.session.add(user)
        
        db.session.commit()
        print(f"✅ აღდგენილია {len(backup_data['users'])} მომხმარებელი")
        
        # Restore comments
        for comment_data in backup_data['comments']:
            comment = Comment(
                content=comment_data['content'],
                project_id=comment_data['project_id'],
                user_id=comment_data['user_id'],
                parent_id=comment_data['parent_id'],
                media_url=comment_data['media_url']
            )
            if comment_data['created_at']:
                comment.created_at = datetime.fromisoformat(comment_data['created_at'])
            db.session.add(comment)
        
        db.session.commit()
        print(f"✅ აღდგენილია {len(backup_data['comments'])} კომენტარი")
        
        # Restore likes
        for like_data in backup_data['likes']:
            like = Like(
                user_id=like_data['user_id'],
                comment_id=like_data['comment_id']
            )
            if like_data['created_at']:
                like.created_at = datetime.fromisoformat(like_data['created_at'])
            db.session.add(like)
        
        db.session.commit()
        print(f"✅ აღდგენილია {len(backup_data['likes'])} ლაიქი")
        
        print("🎉 Database წარმატებით აღდგენილია!")
        return True

if __name__ == "__main__":
    print("📦 DATABASE BACKUP & RESTORE TOOL")
    print("=" * 50)
    print("1. Backup შექმნა")
    print("2. Backup-დან აღდგენა")
    print("3. გასვლა")
    
    choice = input("\nარჩეულება (1-3): ")
    
    if choice == '1':
        backup_database()
    elif choice == '2':
        print("\nარსებული backup ფაილები:")
        backups = [f for f in os.listdir('.') if f.startswith('database_backup_') and f.endswith('.json')]
        if backups:
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup}")
            try:
                selection = int(input(f"აირჩიეთ backup (1-{len(backups)}): ")) - 1
                if 0 <= selection < len(backups):
                    restore_database(backups[selection])
                else:
                    print("❌ არასწორი არჩევანი")
            except ValueError:
                print("❌ არასწორი არჩევანი")
        else:
            print("❌ backup ფაილები ვერ მოიძებნა")
    elif choice == '3':
        print("👋 ნახვამდის!")
    else:
        print("❌ არასწორი არჩევანი")