import os
import sys
sys.path.insert(0, '.')
from flask import Flask
from models import db, Project
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db_projects = Project.query.all()
    print('Projects in database:')
    for p in db_projects:
        print(f'  ID: "{p.id}", Title: {p.title[:30]}...')
        # Test project_id generation
        test_id = secure_filename(p.title.lower().replace(' ', '_'))
        print(f'    Would generate ID: "{test_id}" (len: {len(test_id)})')

print('\nProjects in JSON:')
try:
    with open('projects.json', 'r', encoding='utf-8') as f:
        json_projects = json.load(f)
    print(f'JSON has {len(json_projects)} projects')
    for p in json_projects[-3:]:  # Last 3
        print(f'  ID: "{p.get("id")}", Title: {p.get("title", "")[:30]}...')
except Exception as e:
    print(f'Error reading JSON: {e}')