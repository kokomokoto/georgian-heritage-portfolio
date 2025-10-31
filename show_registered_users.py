#!/usr/bin/env python3
"""
Script to show all registered users from the database
დარეგისტრირებული მომხმარებლების სია
"""

import sqlite3
import os
from datetime import datetime

def show_registered_users():
    """Show all registered users from the database"""
    
    # Database path
    db_path = os.path.join('instance', 'portfolio.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found at:", db_path)
        return
    
    print("📍 დარეგისტრირებული მომხმარებლების ბაზა:")
    print(f"   {os.path.abspath(db_path)}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("""
            SELECT id, name, email, created_at, is_admin
            FROM user 
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("👥 ჯერ არცერთი მომხმარებელი არ დარეგისტრირებულა")
            return
        
        print(f"👥 დარეგისტრირებული მომხმარებლები: {len(users)} ადამიანი")
        print()
        
        for user_id, name, email, created_at, is_admin in users:
            print(f"🆔 ID: {user_id}")
            print(f"👤 სახელი: {name}")
            print(f"📧 ემეილი: {email}")
            print(f"⏰ რეგისტრაციის თარიღი: {created_at}")
            print(f"👑 ადმინი: {'კი' if is_admin else 'არა'}")
            
            # Count user's comments
            cursor.execute("SELECT COUNT(*) FROM comment WHERE user_id = ?", (user_id,))
            comment_count = cursor.fetchone()[0]
            print(f"💬 კომენტარების რაოდენობა: {comment_count}")
            
            # Count user's likes
            cursor.execute("SELECT COUNT(*) FROM like WHERE user_id = ?", (user_id,))
            like_count = cursor.fetchone()[0]
            print(f"👍 ლაიქების რაოდენობა: {like_count}")
            
            print("-" * 40)
        
        # Show database statistics
        print("\n📊 ბაზის სტატისტიკა:")
        
        cursor.execute("SELECT COUNT(*) FROM comment")
        total_comments = cursor.fetchone()[0]
        print(f"💬 სულ კომენტარები: {total_comments}")
        
        cursor.execute("SELECT COUNT(*) FROM like")
        total_likes = cursor.fetchone()[0]
        print(f"👍 სულ ლაიქები: {total_likes}")
        
        cursor.execute("SELECT COUNT(*) FROM comment WHERE user_id IS NOT NULL")
        registered_comments = cursor.fetchone()[0]
        print(f"🔐 დარეგისტრირებული მომხმარებლების კომენტარები: {registered_comments}")
        
        cursor.execute("SELECT COUNT(*) FROM comment WHERE user_id IS NULL")
        anonymous_comments = cursor.fetchone()[0]
        print(f"👻 ანონიმური კომენტარები: {anonymous_comments}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_database_structure():
    """Show the database structure"""
    print("\n🏗️ ბაზის სტრუქტურა:")
    print("=" * 40)
    
    db_path = os.path.join('instance', 'portfolio.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table_name, in tables:
        print(f"\n📋 ცხრილი: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col_id, col_name, col_type, not_null, default_val, primary_key in columns:
            pk_mark = " 🔑" if primary_key else ""
            required_mark = " ⚠️" if not_null else ""
            print(f"   - {col_name}: {col_type}{pk_mark}{required_mark}")
    
    conn.close()

if __name__ == "__main__":
    show_registered_users()
    show_database_structure()