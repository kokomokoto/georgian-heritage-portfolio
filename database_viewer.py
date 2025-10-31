#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database viewer utility for Georgian Heritage Portfolio
Shows all users, comments, and likes from the database
"""

from app import app, db
from models import User, Comment, Like

def show_database_info():
    """Display comprehensive database information"""
    with app.app_context():
        print("=" * 80)
        print("🏛️  GEORGIAN HERITAGE PORTFOLIO - DATABASE INFO")
        print("=" * 80)
        
        # Users
        users = User.query.all()
        print(f"\n👥 USERS ({len(users)} total):")
        print("-" * 50)
        for user in users:
            status = "✅ ვერიფიცირებული" if user.email_verified else "⏳ მოლოდინში"
            print(f"ID: {user.id:2d} | {user.name:<20} | {user.email:<30} | {status}")
            if user.created_at:
                print(f"      რეგისტრაცია: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Comments
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
        print(f"\n💬 COMMENTS ({len(comments)} total):")
        print("-" * 50)
        for comment in comments:
            author_name = comment.author.name if comment.author else "Unknown"
            author_email = comment.author.email if comment.author else "N/A"
            content_preview = (comment.content[:50] + "...") if comment.content and len(comment.content) > 50 else (comment.content or "")
            
            print(f"ID: {comment.id:2d} | პროექტი: {comment.project_id}")
            print(f"      ავტორი: {author_name} ({author_email})")
            print(f"      შიგთავსი: '{content_preview}'")
            print(f"      მედია: {comment.media_url or 'არ არის'}")
            print(f"      პარენტი: {comment.parent_id or 'მთავარი კომენტარი'}")
            print(f"      ლაიქები: {comment.get_like_count()}")
            if comment.created_at:
                print(f"      თარიღი: {comment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Likes
        likes = Like.query.order_by(Like.created_at.desc()).all()
        print(f"\n❤️ LIKES ({len(likes)} total):")
        print("-" * 50)
        for like in likes:
            user_name = like.user.name if like.user else "Unknown"
            comment_preview = ""
            if like.comment:
                if like.comment.content:
                    comment_preview = (like.comment.content[:30] + "...") if len(like.comment.content) > 30 else like.comment.content
                else:
                    comment_preview = "[მედია მხოლოდ]"
                comment_author = like.comment.author.name if like.comment.author else "Unknown"
            else:
                comment_preview = "[კომენტარი წაშლილია]"
                comment_author = "N/A"
            
            print(f"ID: {like.id:2d} | მომხმარებელი: {user_name}")
            print(f"      კომენტარი: '{comment_preview}' (ავტორი: {comment_author})")
            if like.created_at:
                print(f"      თარიღი: {like.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Summary
        print("=" * 80)
        print("📊 SUMMARY:")
        verified_users = len([u for u in users if u.email_verified])
        unverified_users = len(users) - verified_users
        main_comments = len([c for c in comments if not c.parent_id])
        reply_comments = len(comments) - main_comments
        comments_with_media = len([c for c in comments if c.media_url])
        
        print(f"   👥 მომხმარებლები: {len(users)} (ვერიფიცირებული: {verified_users}, მოლოდინში: {unverified_users})")
        print(f"   💬 კომენტარები: {len(comments)} (მთავარი: {main_comments}, პასუხები: {reply_comments})")
        print(f"   🖼️  მედიით კომენტარები: {comments_with_media}")
        print(f"   ❤️  ლაიქები: {len(likes)}")
        print("=" * 80)

if __name__ == "__main__":
    show_database_info()