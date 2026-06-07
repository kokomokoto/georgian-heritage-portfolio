@echo off
echo ========================================
echo  ავტომატური სინქრონიზაცია
echo ========================================
echo.

cd /d "%~dp0"

echo 1. ლოკალური პროექტების ექსპორტი...
python -c "
import sqlite3
import json

conn = sqlite3.connect('instance/portfolio_dev.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM project')
columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

projects = []
for row in rows:
    project = {}
    for i, col in enumerate(columns):
        if col in ['other_images', 'documents', 'project_info', 'type_categories', 'period_categories', 'model_urls']:
            try:
                project[col] = json.loads(row[i]) if row[i] else []
            except:
                project[col] = []
        else:
            project[col] = row[i]
    projects.append(project)

with open('local_projects.json', 'w', encoding='utf-8') as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)

print(f'ექსპორტირებულია {len(projects)} პროექტი')
conn.close()
"

echo.
echo 2. ფაილი გადმოწერეთ ცოცხალ საიტიდან...
echo    გახსენით ბრაუზერში: https://your-render-url.onrender.com/admin/export-projects
echo    შეინახეთ JSON ფაილი როგორც production_projects.json
echo.
echo 3. დააჭირეთ ნებისმიერ ღილაკს როდესაც გადმოწერთ ფაილს...
pause

echo.
echo 4. პროდაქშენის პროექტების იმპორტი...
python migrate_projects_to_db.py

echo.
echo 5. შემოწმება...
python -c "
from app import load_projects
projects = load_projects()
print(f'სულ პროექტი: {len(projects)}')
for p in sorted(projects, key=lambda x: x['title']):
    print(f'- {p[\"title\"]}')
"

echo.
echo დასრულდა! დააჭირეთ ნებისმიერ ღილაკს...
pause