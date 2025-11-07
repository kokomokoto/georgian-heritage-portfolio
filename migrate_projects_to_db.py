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

def migrate_projects_to_db():
    """Migrate projects from projects.json to database"""

    # Initialize Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///portfolio.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if projects already exist in database
        existing_projects = Project.query.count()
        if existing_projects > 0:
            print(f"⚠️  Database already has {existing_projects} projects. Skipping migration.")
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
            project = Project(
                id=project_data['id'],
                title=project_data['title'],
                main_image=project_data.get('main_image'),
                other_images=json.dumps(project_data.get('other_images', [])),
                viewer3D=project_data.get('viewer3D'),
                description=project_data.get('description'),
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