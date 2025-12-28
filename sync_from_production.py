#!/usr/bin/env python3
"""
Script to sync projects from production database to local development database.
This copies all projects from the production PostgreSQL to local SQLite.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def sync_projects_from_production():
    """Sync projects from production to local development"""

    # Import here to avoid running the app
    from app import app, db, Project

    # Get production database URL
    production_db_url = os.environ.get('DATABASE_URL')
    if not production_db_url:
        print("❌ PRODUCTION DATABASE_URL not found in environment variables")
        return

    print("🔄 Starting sync from production to local development...")

    # Configure for production temporarily
    app.config['SQLALCHEMY_DATABASE_URI'] = production_db_url

    try:
        with app.app_context():
            # Connect to production and get all projects
            print("📥 Fetching projects from production database...")
            production_projects = Project.query.all()
            print(f"📊 Found {len(production_projects)} projects in production")

            # Switch back to development database
            dev_db_path = os.path.join(os.getcwd(), 'instance', 'portfolio_dev.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{dev_db_path}'

            # Clear existing projects in dev
            print("🧹 Clearing existing projects in development database...")
            Project.query.delete()
            db.session.commit()

            # Copy projects from production to development
            print("📤 Copying projects to development database...")
            for prod_proj in production_projects:
                dev_proj = Project(
                    id=prod_proj.id,
                    title=prod_proj.title,
                    main_image=prod_proj.main_image,
                    main_image_caption=prod_proj.main_image_caption,
                    other_images=prod_proj.other_images,
                    model_urls=prod_proj.model_urls,
                    viewer3D=prod_proj.viewer3D,
                    description=prod_proj.description,
                    description_file=prod_proj.description_file,
                    folder=prod_proj.folder,
                    latitude=prod_proj.latitude,
                    longitude=prod_proj.longitude,
                    sort_order=prod_proj.sort_order,
                    documents=prod_proj.documents,
                    loading_video=prod_proj.loading_video,
                    loading_audio=prod_proj.loading_audio,
                    project_info=prod_proj.project_info,
                    type_categories=prod_proj.type_categories,
                    period_categories=prod_proj.period_categories,
                    created_at=prod_proj.created_at,
                    updated_at=prod_proj.updated_at
                )
                db.session.add(dev_proj)

            db.session.commit()
            print(f"✅ Successfully synced {len(production_projects)} projects to development database")

    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    sync_projects_from_production()