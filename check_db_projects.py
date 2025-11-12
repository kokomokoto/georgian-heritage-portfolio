from app import app
from models import Project

app.app_context().push()
projects = Project.query.all()

print('პროექტების რაოდენობა მონაცემთა ბაზაში:', len(projects))
print('პროექტები:')
for p in projects:
    print(f'  - {p.title}')