import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

LIVE_URL = os.environ.get('LIVE_SITE_URL', 'https://georgian-heritage-portfolio-1.onrender.com/').rstrip('/') + '/'
SYNC_TOKEN = os.environ.get('SYNC_EXPORT_TOKEN', '')


def _export_params():
    if SYNC_TOKEN:
        return {'token': SYNC_TOKEN}
    return {}


def sync_projects_from_live():
    """Sync projects from live site to local projects.json"""
    try:
        response = requests.get(
            f'{LIVE_URL}export-projects',
            params=_export_params(),
            timeout=30,
        )
        response.raise_for_status()

        projects_data = response.json()

        # Save to local projects.json
        with open('projects.json', 'w', encoding='utf-8') as f:
            json.dump(projects_data, f, ensure_ascii=False, indent=2)

        print(f"Successfully synced {len(projects_data)} projects from live site to projects.json")

    except Exception as e:
        print(f"Error syncing projects: {e}")

def sync_comments_from_live():
    """Sync comments from live site to local comments.json"""
    try:
        # Fetch comments from live export endpoint
        response = requests.get(
            f'{LIVE_URL}export-comments',
            params=_export_params(),
            timeout=30,
        )
        response.raise_for_status()

        comments_data = response.json()

        # Save to local comments.json
        with open('comments.json', 'w', encoding='utf-8') as f:
            json.dump(comments_data, f, ensure_ascii=False, indent=2)

        print(f"Successfully synced comments from live site to comments.json")

    except Exception as e:
        print(f"Error syncing comments: {e}")

if __name__ == '__main__':
    sync_projects_from_live()
    sync_comments_from_live()