import requests
import json
import os

# Replace with your live site URL
LIVE_URL = 'https://your-live-site.onrender.com'  # IMPORTANT: Update this with your actual live URL!

def sync_projects_from_live():
    """Sync projects from live site to local projects.json"""
    try:
        # Fetch projects from live export endpoint
        response = requests.get(f'{LIVE_URL}/export-projects', timeout=30)
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
        response = requests.get(f'{LIVE_URL}/export-comments', timeout=30)
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