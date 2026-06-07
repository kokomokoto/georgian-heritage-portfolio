#!/usr/bin/env python3
"""
Migration script to move projects from JSON file to database
"""
import os
import json
import sys
from flask import Flask
from models import db, Project

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def migrate_projects_to_db():
    """Migrate projects from projects.json to database"""

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
        # Create tables if they don't exist
        db.create_all()

        # Check if projects already exist in database
        existing_projects = Project.query.all()
        if existing_projects:
            print(f"⚠️  Database already has {len(existing_projects)} projects.")
            # Update descriptions if empty
            updated = 0
            for project in existing_projects:
                if not project.description and project.description_file:
                    desc_path = os.path.join('projects', project.folder, 'description.txt')
                    if os.path.exists(desc_path):
                        with open(desc_path, 'r', encoding='utf-8') as f:
                            project.description = f.read()
                            updated += 1
                            print(f"✅ Updated description for: {project.title}")
            if updated > 0:
                db.session.commit()
                print(f"🎉 Updated descriptions for {updated} projects!")
            return

        # Load projects from JSON
        projects_json = 'projects.json'
        if not os.path.exists(projects_json):
            print("❌ projects.json not found!")
            return

        with open(projects_json, 'r', encoding='utf-8') as f:
            projects_data = json.load(f)

        print(f"📁 Found {len(projects_data)} projects in JSON file")

        # Migrate each project
        for project_data in projects_data:
            # Read description from file if exists
            description = ''
            if project_data.get('description_file'):
                desc_path = os.path.join('projects', project_data.get('folder', ''), 'description.txt')
                if os.path.exists(desc_path):
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        description = f.read()
            
            project = Project(
                id=project_data['id'],
                title=project_data['title'],
                main_image=project_data.get('main_image'),
                other_images=json.dumps(project_data.get('other_images', [])),
                viewer3D=project_data.get('viewer3D'),
                description=description,
                description_file=project_data.get('description_file'),
                folder=project_data.get('folder'),
                latitude=project_data.get('latitude'),
                longitude=project_data.get('longitude'),
                documents=json.dumps(project_data.get('documents', [])),
                loading_video=project_data.get('loading_video'),
                loading_audio=project_data.get('loading_audio'),
                project_info=json.dumps(project_data.get('project_info', {})),
                type_categories=json.dumps(project_data.get('type_categories', [])),
                period_categories=json.dumps(project_data.get('period_categories', []))
            )

            db.session.add(project)
            print(f"✅ Migrated project: {project.title}")

        # Commit all changes
        db.session.commit()
        print(f"🎉 Successfully migrated {len(projects_data)} projects to database!")

if __name__ == '__main__':
    migrate_projects_to_db()