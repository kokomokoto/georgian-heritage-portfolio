from app import app, db, PROJECTS_DIR
from models import Project
import os
import json

def restore_projects():
    """Restore projects from existing folders"""

    with app.app_context():
        print("Restoring projects from folders...")

        # Get existing project IDs in database
        existing_ids = {p.id for p in Project.query.all()}
        print(f"Existing project IDs: {existing_ids}")

        # Find all project folders
        projects_dir = PROJECTS_DIR
        restored_count = 0

        for item in os.listdir(projects_dir):
            folder_path = os.path.join(projects_dir, item)
            if os.path.isdir(folder_path) and item.startswith('project_'):
                project_id = item

                # Skip if already exists
                if project_id in existing_ids:
                    print(f"⚠️  {project_id} already exists, skipping")
                    continue

                # Check if description.txt exists
                desc_file = os.path.join(folder_path, 'description.txt')
                if not os.path.exists(desc_file):
                    print(f"❌ {project_id} missing description.txt, skipping")
                    continue

                # Read description
                with open(desc_file, 'r', encoding='utf-8') as f:
                    description = f.read().strip()

                # Create basic project entry
                # We'll use a generic title based on the folder name
                title = f"პროექტი {project_id.split('_')[1]}"  # e.g., "პროექტი 5"

                project = Project(
                    id=project_id,
                    title=title,
                    description=description,
                    description_file='description.txt',
                    folder=project_id,
                    sort_order=int(project_id.split('_')[1])  # Use project number as sort order
                )

                db.session.add(project)
                restored_count += 1
                print(f"✅ Restored {project_id}: {title}")

        if restored_count > 0:
            db.session.commit()
            print(f"🎉 Successfully restored {restored_count} projects!")
        else:
            print("ℹ️  No new projects to restore")

if __name__ == "__main__":
    restore_projects()