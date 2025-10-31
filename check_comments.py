from app import app
from models import Comment

app.app_context().push()

# Get comments for project_3
comments = Comment.query.filter_by(project_id='project_3').all()
print(f'Found {len(comments)} comments for project_3')

for i, c in enumerate(comments[:10], 1):
    print(f'{i}. Comment {c.id}:')
    print(f'   Content: "{c.content}"')
    print(f'   Media URL: "{c.media_url}"')
    print(f'   Media URL type: {type(c.media_url)}')
    print(f'   Media URL is None: {c.media_url is None}')
    print(f'   Media URL == "None": {c.media_url == "None"}')
    print(f'   Has media (bool check): {bool(c.media_url)}')
    if c.media_url and c.media_url != "None":
        print(f'   ✅ HAS VALID MEDIA URL')
    else:
        print(f'   ❌ NO VALID MEDIA URL')
    print()