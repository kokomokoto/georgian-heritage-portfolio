#!/usr/bin/env python3
"""
Simple app check script to test basic functionality
"""
import os
import sys

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'DATABASE_URL',
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY', 
        'CLOUDINARY_API_SECRET'
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import flask
        import sqlalchemy
        import cloudinary
        print("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test basic database connection"""
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///test.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            # Try to execute a simple query
            db.engine.execute('SELECT 1')
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Running simple app checks...")
    
    checks = [
        test_imports(),
        check_environment(), 
        test_database_connection()
    ]
    
    if all(checks):
        print("🎉 All checks passed! App should work fine.")
        sys.exit(0)
    else:
        print("💥 Some checks failed. Fix issues before deploying.")
        sys.exit(1)