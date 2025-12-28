#!/usr/bin/env python3
"""
Check current projects on production site
"""
import requests

try:
    response = requests.get('https://georgian-heritage-portfolio-1.onrender.com/export-projects', timeout=30)
    if response.status_code == 200:
        projects = response.json()
        print(f'ონლაინ საიტზე არის {len(projects)} პროექტი')
        for p in projects:
            print(f'  - {p["id"]}: {p["title"]}')
    else:
        print(f'შეცდომა: {response.status_code}')
        print(f'პასუხი: {response.text}')
except Exception as e:
    print(f'შეცდომა: {e}')