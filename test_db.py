import os
print("Current working directory:", os.getcwd())

# Import models first
from models import db, Project, User, Comment, Like

# Create a minimal Flask app for testing
from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])

    # Try to create tables manually with raw SQL
    import sqlite3
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()

    # Create project table manually
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            main_image TEXT,
            main_image_caption TEXT,
            other_images TEXT,
            "viewer3D" TEXT,
            description TEXT,
            description_file TEXT,
            folder TEXT,
            latitude TEXT,
            longitude TEXT,
            documents TEXT,
            loading_video TEXT,
            loading_audio TEXT,
            project_info TEXT,
            type_categories TEXT,
            period_categories TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create user table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email_verified BOOLEAN DEFAULT 0,
            verification_token TEXT,
            reset_token TEXT,
            reset_token_expires DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Create comment table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            project_id TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (project_id) REFERENCES project (id)
        )
    ''')

    # Create like table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "like" (
            id INTEGER PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            project_id TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (project_id) REFERENCES project (id)
        )
    ''')

    conn.commit()
    print("Tables created manually with raw SQL")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("All tables:", [t[0] for t in tables])

    if any(t[0] == 'project' for t in tables):
        print("Project table exists")
        cursor.execute("PRAGMA table_info(project)")
        columns = cursor.fetchall()
        print("Columns:", [col[1] for col in columns])
        if 'sort_order' in [col[1] for col in columns]:
            print("✅ sort_order column exists!")
        else:
            print("❌ sort_order column missing!")
    else:
        print("Project table does not exist")
    conn.close()