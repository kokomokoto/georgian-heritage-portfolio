import json

with open('projects.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print('Projects in JSON:', len(data))
    for i, project in enumerate(data):
        print(f"{i+1}. {project['title']}")