"""
Import production projects data from projects_data.js into local SQLite database.
Run this ONCE to populate your local database with all 13 production projects.

Usage: python import_to_local_db.py
"""
import os
import sys
import json
import re

# Set up Flask app context
os.environ.pop('DATABASE_URL', None)  # Force local SQLite
os.environ.pop('POSTGRESQL_DATABASE_URL', None)
os.environ.pop('DB_CONNECTION_STRING', None)

from app import app, db
from models import Project, SiteSetting

PROJECTS_DATA_JS = os.path.join(os.path.dirname(__file__), '_cloudflare_static', 'projects_data.js')

def parse_projects_data_js(filepath):
    """Parse projects_data.js and extract JSON array"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove "var projectsData = " prefix and trailing semicolon
    match = re.search(r'var\s+projectsData\s*=\s*(\[.*\])\s*;?\s*$', content, re.DOTALL)
    if not match:
        print("❌ Could not parse projects_data.js")
        sys.exit(1)
    
    return json.loads(match.group(1))


def import_projects():
    """Import all projects from projects_data.js into local SQLite"""
    if not os.path.exists(PROJECTS_DATA_JS):
        print(f"❌ File not found: {PROJECTS_DATA_JS}")
        sys.exit(1)
    
    projects = parse_projects_data_js(PROJECTS_DATA_JS)
    print(f"📄 Found {len(projects)} projects in projects_data.js")
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        imported = 0
        updated = 0
        
        for p in projects:
            project_id = p.get('id', '')
            existing = Project.query.get(project_id)
            
            if existing:
                # Update existing project
                existing.title = p.get('title', '')
                existing.main_image = p.get('main_image')
                existing.main_image_caption = p.get('main_image_caption')
                existing.other_images = json.dumps(p.get('other_images', []), ensure_ascii=False) if p.get('other_images') else None
                existing.model_urls = json.dumps(p.get('model_urls', []), ensure_ascii=False) if p.get('model_urls') else None
                existing.viewer3D = p.get('viewer3D')
                existing.description = p.get('description')
                existing.description_file = p.get('description_file')
                existing.folder = p.get('folder')
                existing.latitude = str(p.get('latitude')) if p.get('latitude') else None
                existing.longitude = str(p.get('longitude')) if p.get('longitude') else None
                existing.sort_order = p.get('sort_order', 0)
                existing.documents = json.dumps(p.get('documents', []), ensure_ascii=False) if p.get('documents') else None
                existing.loading_video = p.get('loading_video')
                existing.loading_audio = p.get('loading_audio')
                existing.project_info = json.dumps(p.get('project_info', {}), ensure_ascii=False) if p.get('project_info') else None
                existing.type_categories = json.dumps(p.get('type_categories', []), ensure_ascii=False) if p.get('type_categories') else None
                existing.period_categories = json.dumps(p.get('period_categories', []), ensure_ascii=False) if p.get('period_categories') else None
                updated += 1
                print(f"  🔄 Updated: {p.get('title', project_id)}")
            else:
                # Create new project
                new_project = Project(
                    id=project_id,
                    title=p.get('title', ''),
                    main_image=p.get('main_image'),
                    main_image_caption=p.get('main_image_caption'),
                    other_images=json.dumps(p.get('other_images', []), ensure_ascii=False) if p.get('other_images') else None,
                    model_urls=json.dumps(p.get('model_urls', []), ensure_ascii=False) if p.get('model_urls') else None,
                    viewer3D=p.get('viewer3D'),
                    description=p.get('description'),
                    description_file=p.get('description_file'),
                    folder=p.get('folder'),
                    latitude=str(p.get('latitude')) if p.get('latitude') else None,
                    longitude=str(p.get('longitude')) if p.get('longitude') else None,
                    sort_order=p.get('sort_order', 0),
                    documents=json.dumps(p.get('documents', []), ensure_ascii=False) if p.get('documents') else None,
                    loading_video=p.get('loading_video'),
                    loading_audio=p.get('loading_audio'),
                    project_info=json.dumps(p.get('project_info', {}), ensure_ascii=False) if p.get('project_info') else None,
                    type_categories=json.dumps(p.get('type_categories', []), ensure_ascii=False) if p.get('type_categories') else None,
                    period_categories=json.dumps(p.get('period_categories', []), ensure_ascii=False) if p.get('period_categories') else None,
                )
                db.session.add(new_project)
                imported += 1
                print(f"  ✅ Imported: {p.get('title', project_id)}")
        
        # Also set the home 3D viewer setting
        home_viewer = SiteSetting.query.get('home_3d_viewer')
        if not home_viewer:
            home_viewer = SiteSetting(
                key='home_3d_viewer',
                value='<iframe id="viewer" width="100%" height="225" allow="fullscreen; xr-spatial-tracking" src="https://superspl.at/s?id=4aeaa171"></iframe>'
            )
            db.session.add(home_viewer)
            print("  ✅ Set home 3D viewer setting")
        
        db.session.commit()
        
        total = Project.query.count()
        print(f"\n🎉 Done! Imported: {imported}, Updated: {updated}, Total in DB: {total}")


if __name__ == '__main__':
    import_projects()
