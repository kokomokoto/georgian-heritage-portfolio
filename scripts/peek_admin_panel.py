"""Fetch admin panel after login and print visible content."""
import re
import sys

import requests

s = requests.Session()
base = "http://127.0.0.1:5002"

r = s.post(
    f"{base}/admin",
    data={"username": "kepulia", "password": "kepulia123"},
    allow_redirects=True,
)
print("After login:", r.url)

r2 = s.get(f"{base}/admin/panel")
html = r2.text
print("Panel status:", r2.status_code, "| URL:", r2.url)

if "login" in r2.url.lower() and "panel" not in r2.url:
    print("FAILED: still on login page")
    sys.exit(1)

h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
if h1:
    print("H1:", re.sub(r"<[^>]+>", "", h1.group(1)).strip())

card_headers = re.findall(r"<strong>([^<]+)</strong>", html)
for t in card_headers[:6]:
    t = t.strip()
    if t:
        print("Section:", t)

ths = re.findall(r"<thead[^>]*>.*?<th[^>]*>(.*?)</th>", html, re.S)
if ths:
    cols = [re.sub(r"<[^>]+>", "", x).strip() for x in ths]
    print("Columns:", cols)

rows = re.findall(r'<tr data-id="([^"]+)">(.*?)</tr>', html, re.S)
print(f"Projects: {len(rows)}")
for i, (pid, row) in enumerate(rows):
    cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
    title = re.sub(r"<[^>]+>", "", cells[2] if len(cells) > 2 else "").strip() if cells else "?"
    print(f"  {i+1}. {title} (id={pid})")

print("Drag-drop:", "bi-grip-vertical" in html and "sortablejs" in html.lower())
