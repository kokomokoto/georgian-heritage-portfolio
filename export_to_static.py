"""
Export projects from local SQLite database to projects_data.js for the static site.
Run this after making changes in the admin panel to update the Cloudflare Pages site.

Usage: python export_to_static.py
Then:  cd _cloudflare_static && git add -A && git commit -m "Update projects" && git push
"""
import os
import sys
import json

# Force local SQLite mode
os.environ.pop('DATABASE_URL', None)
os.environ.pop('POSTGRESQL_DATABASE_URL', None)
os.environ.pop('DB_CONNECTION_STRING', None)

from app import app, db
from models import Project, SiteSetting

STATIC_DIR = os.path.join(os.path.dirname(__file__), '_cloudflare_static')
PROJECTS_DATA_JS = os.path.join(STATIC_DIR, 'projects_data.js')
INDEX_HTML = os.path.join(STATIC_DIR, 'index.html')


def export_projects():
    """Export all projects from local DB to projects_data.js"""
    with app.app_context():
        projects = Project.query.order_by(Project.sort_order.asc(), Project.created_at.desc()).all()
        
        if not projects:
            print("ERROR: No projects found in local database!")
            print("   Run 'python import_to_local_db.py' first to populate the database.")
            sys.exit(1)
        
        result = []
        for p in projects:
            project_dict = {
                'id': p.id,
                'title': p.title,
                'main_image': p.main_image,
                'main_image_caption': p.main_image_caption,
                'other_images': json.loads(p.other_images) if p.other_images else [],
                'model_urls': json.loads(p.model_urls) if p.model_urls else [],
                'viewer3D': p.viewer3D,
                'description': p.description,
                'description_file': p.description_file,
                'folder': p.folder,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'sort_order': p.sort_order,
                'documents': json.loads(p.documents) if p.documents else [],
                'loading_video': p.loading_video,
                'loading_audio': p.loading_audio,
                'project_info': json.loads(p.project_info) if p.project_info else {},
                'type_categories': json.loads(p.type_categories) if p.type_categories else [],
                'period_categories': json.loads(p.period_categories) if p.period_categories else [],
            }
            result.append(project_dict)
        
        # Write projects_data.js
        js_content = "var projectsData = " + json.dumps(result, ensure_ascii=False, indent=2) + ";\n"
        
        with open(PROJECTS_DATA_JS, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        os.makedirs(STATIC_DIR, exist_ok=True)
        print(f"Exported {len(result)} projects to {PROJECTS_DATA_JS}")
        
        # Also update home 3D viewer in index.html if changed
        try:
            home_viewer = SiteSetting.query.get('home_3d_viewer')
            if home_viewer and home_viewer.value:
                update_home_viewer(home_viewer.value)
        except Exception as e:
            print(f"WARNING: Could not update home 3D viewer: {e}")
        
        print("\nNext: run .\\publish.ps1  OR  cd _cloudflare_static && git push")


def update_home_viewer(viewer_html):
    """Update the home 3D viewer iframe in index.html"""
    if not os.path.exists(INDEX_HTML):
        return
    
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find and replace the viewer iframe
    import re
    pattern = r'(<div class="viewer-wrap">)\s*<iframe[^>]*>.*?</iframe>\s*(</div>)'
    replacement = f'\\1\n                {viewer_html}\n            \\2'
    
    new_html, count = re.subn(pattern, replacement, html, flags=re.DOTALL)
    
    if count > 0:
        with open(INDEX_HTML, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("Updated home 3D viewer in index.html")
    else:
        print("WARNING: Could not find viewer-wrap div in index.html (no changes made)")


if __name__ == '__main__':
    export_projects()
