import json

with open('projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('პროექტების რაოდენობა JSON-ში:', len(data))
print('პროექტები:')
for p in data:
    print(f'  - {p["title"]}')