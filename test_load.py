from app import app, load_projects

app.app_context().push()
projects = load_projects()

print('პროექტების რაოდენობა:', len(projects))
print('პირველი 3 პროექტი:')
for p in projects[:3]:
    print(f'  - {p["title"]}')