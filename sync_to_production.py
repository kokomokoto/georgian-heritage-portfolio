#!/usr/bin/env python3
"""
Script to sync projects from local development database to production database.
This copies all projects from the local SQLite to the production PostgreSQL.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def sync_projects_to_production():
    """Sync projects from local development to production"""

    # Import here to avoid running the app
    from app import app, db, Project

    # Get production database URL
    production_db_url = os.environ.get('DATABASE_URL')
    if not production_db_url:
        print("❌ PRODUCTION DATABASE_URL not found in environment variables")
        return

    print("🔄 Starting sync from local development to production...")

    # First, get all projects from local database
    local_db_path = os.path.join(os.getcwd(), 'instance', 'portfolio.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{local_db_path}'

    try:
        with app.app_context():
            # Connect to local and get all projects
            print("📥 Fetching projects from local database...")
            local_projects = Project.query.all()
            print(f"📊 Found {len(local_projects)} projects in local database")

            if len(local_projects) == 0:
                print("❌ No projects found in local database!")
                return

            # Switch to production database
            app.config['SQLALCHEMY_DATABASE_URI'] = production_db_url

            # Clear existing projects in production (optional - be careful!)
            print("⚠️  This will REPLACE all projects in production!")
            confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
            if confirm.lower() != 'yes':
                print("❌ Sync cancelled by user")
                return

            print("🧹 Clearing existing projects in production database...")
            Project.query.delete()
            db.session.commit()

            # Copy projects from local to production
            print("📤 Copying projects to production database...")
            for local_proj in local_projects:
                prod_proj = Project(
                    id=local_proj.id,
                    title=local_proj.title,
                    main_image=local_proj.main_image,
                    main_image_caption=local_proj.main_image_caption,
                    other_images=local_proj.other_images,
                    model_urls=local_proj.model_urls,
                    viewer3D=local_proj.viewer3D,
                    description=local_proj.description,
                    description_file=local_proj.description_file,
                    folder=local_proj.folder,
                    latitude=local_proj.latitude,
                    longitude=local_proj.longitude,
                    sort_order=local_proj.sort_order,
                    documents=local_proj.documents,
                    loading_video=local_proj.loading_video,
                    loading_audio=local_proj.loading_audio,
                    project_info=local_proj.project_info,
                    type_categories=local_proj.type_categories,
                    period_categories=local_proj.period_categories,
                    created_at=local_proj.created_at,
                    updated_at=local_proj.updated_at
                )
                db.session.add(prod_proj)

            db.session.commit()
            print(f"✅ Successfully synced {len(local_projects)} projects to production database")

            # Verify the sync
            production_count = Project.query.count()
            print(f"✅ Verification: Production database now has {production_count} projects")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    sync_projects_to_production()