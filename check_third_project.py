import json

with open('projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Third project:')
print(json.dumps(data[2], indent=2, ensure_ascii=False))