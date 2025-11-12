from app import app, db, PROJECTS_DIR, PROJECTS_JSON
from models import Project
import json
import os

with app.app_context():
    print("Seeding database with initial projects...")
    try:
        if Project.query.count() == 0:
            with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
            for proj_data in projects_data:
                description = ""
                if proj_data.get('description_file'):
                    desc_path = os.path.join(PROJECTS_DIR, proj_data['folder'], proj_data['description_file'])
                    if os.path.exists(desc_path):
                        with open(desc_path, 'r', encoding='utf-8') as df:
                            description = df.read()
                project = Project(
                    id=proj_data['id'],
                    title=proj_data['title'],
                    main_image=proj_data.get('main_image'),
                    other_images=json.dumps(proj_data.get('other_images', [])),
                    viewer3D=proj_data.get('viewer3D'),
                    description=description,
                    description_file=proj_data.get('description_file'),
                    folder=proj_data.get('folder'),
                    latitude=proj_data.get('latitude'),
                    longitude=proj_data.get('longitude'),
                    documents=json.dumps(proj_data.get('documents', [])),
                    loading_video=proj_data.get('loading_video'),
                    loading_audio=proj_data.get('loading_audio'),
                    project_info=json.dumps(proj_data.get('project_info', {})),
                    type_categories=json.dumps(proj_data.get('type_categories', [])),
                    period_categories=json.dumps(proj_data.get('period_categories', [])),
                    sort_order=0  # Default sort order
                )
                db.session.add(project)
            db.session.commit()
            print("✅ Seeded database with initial projects")
        else:
            print("Database already has projects")
    except Exception as e:
        print(f"Error seeding database: {e}")