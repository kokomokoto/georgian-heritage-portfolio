from app import app
from models import Comment

app.app_context().push()

# Get one specific comment with media
comment = Comment.query.filter(Comment.media_url.isnot(None)).first()

if comment:
    print(f"Found comment with media:")
    print(f"ID: {comment.id}")
    print(f"Content: '{comment.content}'")
    print(f"Media URL: '{comment.media_url}'")
    print(f"Project ID: '{comment.project_id}'")
    print(f"\nTesting URL accessibility...")
    
    import requests
    try:
        response = requests.head(comment.media_url, timeout=10)
        print(f"URL Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print("✅ URL is accessible")
    except Exception as e:
        print(f"❌ URL error: {e}")
else:
    print("No comments with media found")