# PowerShell script for automatic sync
Write-Host "========================================" -ForegroundColor Green
Write-Host " ავტომატური სინქრონიზაცია" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "1. ლოკალური პროექტების ექსპორტი..." -ForegroundColor Yellow
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

Write-Host ""
Write-Host "2. ახლა გახსენით ბრაუზერში ეს მისამართი:" -ForegroundColor Cyan
Write-Host "   https://your-render-url.onrender.com/admin/export-projects" -ForegroundColor White
Write-Host ""
Write-Host "3. შეინახეთ JSON ფაილი როგორც 'production_projects.json'" -ForegroundColor Cyan
Write-Host ""
Read-Host "დააჭირეთ Enter როდესაც გადმოწერთ ფაილს"

Write-Host ""
Write-Host "4. პროდაქშენის პროექტების იმპორტი..." -ForegroundColor Yellow
python migrate_projects_to_db.py

Write-Host ""
Write-Host "5. შემოწმება..." -ForegroundColor Yellow
python -c "
from app import load_projects
projects = load_projects()
print(f'სულ პროექტი: {len(projects)}')
for p in sorted(projects, key=lambda x: x['title']):
    print(f'- {p[\"title\"]}')
"

Write-Host ""
Write-Host "დასრულდა!" -ForegroundColor Green
Read-Host "დააჭირეთ Enter დასასრულებლად"