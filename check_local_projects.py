#!/usr/bin/env python3
"""
Check current projects in local database
"""
from app import app, load_projects

with app.app_context():
    projects = load_projects()
    print(f'ლოკალურად არის {len(projects)} პროექტი')
    for p in projects:
        print(f'  - {p["id"]}: {p["title"]}')