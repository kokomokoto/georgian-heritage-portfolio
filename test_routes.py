from app import app

with app.test_client() as client:
    # Test home page
    response = client.get('/')
    print(f'✅ Home page: {response.status_code}')

    # Test admin page
    response = client.get('/admin')
    print(f'✅ Admin page: {response.status_code}')

    # Test project pages
    from app import load_projects
    app.app_context().push()
    projects = load_projects()
    if projects:
        response = client.get(f'/project/{projects[0]["id"]}')
        print(f'✅ Project page: {response.status_code}')
    else:
        print('⚠️  No projects to test')

print('✅ Basic routing tests completed')