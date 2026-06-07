#!/usr/bin/env python3
import zipfile
import os

# Create a test ZIP file
with zipfile.ZipFile('test_3d_model.zip', 'w') as zf:
    # Add HTML file
    html_content = '''<!DOCTYPE html>
<html>
<head><title>Test 3D Model</title></head>
<body>
    <h1>Test 3D Viewer</h1>
    <script src="script.js"></script>
    <link rel="stylesheet" href="style.css">
    <div id="model-container">3D Model would load here</div>
</body>
</html>'''
    zf.writestr('index.html', html_content)

    # Add JS file
    js_content = 'console.log("Test 3D viewer loaded");'
    zf.writestr('script.js', js_content)

    # Add CSS file
    css_content = 'body { background: #f0f0f0; color: #333; }'
    zf.writestr('style.css', css_content)

print('Test ZIP file created successfully')