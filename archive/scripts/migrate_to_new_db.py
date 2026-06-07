#!/usr/bin/env python3
"""
Script to migrate data from old database to new database.
This copies all data from the old exposed database to a new secure database.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_to_new_database():
    """Migrate all data from old database to new database"""

    # OLD DATABASE (exposed credentials) - set in .env as OLD_DATABASE_URL
    old_db_url = os.environ.get('OLD_DATABASE_URL')
    if not old_db_url:
        print("❌ OLD_DATABASE_URL environment variable not set!")
        print("   Please set OLD_DATABASE_URL to your OLD (exposed) database URL")
        return

    # NEW DATABASE (secure credentials) - prefer NEW_DATABASE_URL; fallback to DATABASE_URL
    # This removes the need to have two apps open or keep switching DATABASE_URL.
    new_db_url = os.environ.get('NEW_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if not new_db_url:
        print("❌ NEW_DATABASE_URL (or DATABASE_URL) environment variable not set!")
        print("   Please set NEW_DATABASE_URL (recommended) to your NEW database URL")
        return

    print("🔄 Starting migration from old to new database...")

    # Import here to avoid running the app
    from app import app, db, Project, Comment, User, Like

    def normalize_postgres_url(url: str) -> str:
        """Ensure the URL uses the same driver as app.py (pg8000)."""
        if not url:
            return url
        if url.startswith('postgresql://'):
            return url.replace('postgresql://', 'postgresql+pg8000://', 1)
        return url

    old_db_url = normalize_postgres_url(old_db_url)
    new_db_url = normalize_postgres_url(new_db_url)

    try:
        # Connect to OLD database and get all data
        print("📥 Connecting to old database...")
        app.config['SQLALCHEMY_DATABASE_URI'] = old_db_url

        with app.app_context():
            print("📊 Fetching data from old database...")

            # Get all data
            projects = Project.query.all()
            comments = Comment.query.all()
            users = User.query.all()
            likes = Like.query.all()

            print(f"📋 Found: {len(projects)} projects, {len(comments)} comments, {len(users)} users, {len(likes)} likes")

            # Switch to NEW database
            print("🔄 Switching to new database...")
            app.config['SQLALCHEMY_DATABASE_URI'] = new_db_url

            # Create all tables in new database
            db.create_all()
            print("✅ New database tables created")

            # Copy all data
            print("📤 Copying projects...")
            for project in projects:
                new_project = Project(
                    id=project.id,
                    title=project.title,
                    main_image=project.main_image,
                    main_image_caption=project.main_image_caption,
                    other_images=project.other_images,
                    model_urls=project.model_urls,
                    viewer3D=project.viewer3D,
                    description=project.description,
                    description_file=project.description_file,
                    folder=project.folder,
                    latitude=project.latitude,
                    longitude=project.longitude,
                    sort_order=project.sort_order,
                    documents=project.documents,
                    loading_video=project.loading_video,
                    loading_audio=project.loading_audio,
                    project_info=project.project_info,
                    type_categories=project.type_categories,
                    period_categories=project.period_categories,
                    created_at=project.created_at
                )
                db.session.add(new_project)

            print("📤 Copying users...")
            for user in users:
                new_user = User(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    email_verified=user.email_verified,
                    password_hash=user.password_hash,
                    created_at=user.created_at
                )
                db.session.add(new_user)

            print("📤 Copying comments...")
            for comment in comments:
                new_comment = Comment(
                    id=comment.id,
                    project_id=comment.project_id,
                    name=comment.name,
                    email=comment.email,
                    message=comment.message,
                    created_at=comment.created_at,
                    is_approved=comment.is_approved
                )
                db.session.add(new_comment)

            print("📤 Copying likes...")
            for like in likes:
                new_like = Like(
                    id=like.id,
                    project_id=like.project_id,
                    ip_address=like.ip_address,
                    created_at=like.created_at
                )
                db.session.add(new_like)

            # Commit all changes
            db.session.commit()
            print("✅ Migration completed successfully!")
            print(f"📊 Migrated: {len(projects)} projects, {len(comments)} comments, {len(users)} users, {len(likes)} likes")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_to_new_database()