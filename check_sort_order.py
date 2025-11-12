from app import app, load_projects

app.app_context().push()
projects = load_projects()

print('Sort order verification:')
print(f'  - Total projects: {len(projects)}')
for i, p in enumerate(projects):
    sort_order = p.get('sort_order', 'Missing')
    print(f'  - Project {i+1}: {p["title"]} (sort_order: {sort_order})')

# Check if sorted correctly
sort_orders = [p.get('sort_order', 0) for p in projects]
is_sorted = all(sort_orders[i] <= sort_orders[i+1] for i in range(len(sort_orders)-1))
print(f'  - Properly sorted by sort_order: {"✅" if is_sorted else "❌"}')