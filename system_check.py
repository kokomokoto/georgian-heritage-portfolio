from app import app, load_projects, ADMIN_USERNAME, ADMIN_PASSWORD
from models import Project, User, Comment, Like
import os

print('🔍 COMPREHENSIVE SYSTEM CHECK')
print('=' * 50)

# 1. App Configuration
print('✅ APP CONFIGURATION:')
print(f'  - SECRET_KEY: {"Set" if app.config["SECRET_KEY"] else "Missing"}')
print(f'  - DATABASE_URI: {app.config["SQLALCHEMY_DATABASE_URI"][:50]}...')
print(f'  - SESSION_COOKIE_DOMAIN: {app.config["SESSION_COOKIE_DOMAIN"]}')
print(f'  - ADMIN_USERNAME: {ADMIN_USERNAME}')
print(f'  - ADMIN_PASSWORD: {"Set (length: " + str(len(ADMIN_PASSWORD)) + ")" if ADMIN_PASSWORD else "Missing"}')

# 2. Database Status
print('\n✅ DATABASE STATUS:')
with app.app_context():
    try:
        projects = Project.query.all()
        users = User.query.all()
        comments = Comment.query.all()
        likes = Like.query.all()
        print(f'  - Projects: {len(projects)}')
        print(f'  - Users: {len(users)}')
        print(f'  - Comments: {len(comments)}')
        print(f'  - Likes: {len(likes)}')
        print('  - Database connection: ✅ Working')
    except Exception as e:
        print(f'  - Database error: ❌ {e}')

# 3. File System
print('\n✅ FILE SYSTEM:')
key_files = ['app.py', 'models.py', 'forms.py', 'requirements.txt', 'static/style.css']
for file in key_files:
    exists = os.path.exists(file)
    print(f'  - {file}: {"✅" if exists else "❌"}')

# 4. Project Folders
print('\n✅ PROJECT FOLDERS:')
projects_dir = 'projects'
if os.path.exists(projects_dir):
    folders = [f for f in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, f))]
    print(f'  - Project folders: {len(folders)} ({", ".join(folders[:3])}{"..." if len(folders) > 3 else ""})')
else:
    print('  - Projects directory: ❌ Missing')

# 5. Load Projects Function
print('\n✅ PROJECT LOADING:')
try:
    with app.app_context():
        projects = load_projects()
        print(f'  - Projects loaded: {len(projects)}')
        if projects:
            print(f'  - First project: {projects[0]["title"]}')
            print(f'  - Sort order working: {"✅" if "sort_order" in str(projects[0]) else "❌"}')
except Exception as e:
    print(f'  - Error loading projects: ❌ {e}')

# 6. Admin Login Test
print('\n✅ ADMIN LOGIN TEST:')
with app.test_client() as client:
    # Test admin page access
    response = client.get('/admin')
    print(f'  - Admin page accessible: {"✅" if response.status_code == 200 else "❌"}')

    # Test login form
    response = client.post('/admin/login', data={
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }, follow_redirects=True)
    login_success = 'admin panel' in response.get_data(as_text=True).lower()
    print(f'  - Admin login works: {"✅" if login_success else "❌"}')

print('\n' + '=' * 50)
print('🎉 SYSTEM CHECK COMPLETE!')
print('If all items show ✅, the system is ready for use.')
print('You can now safely re-upload your projects through the admin panel.')