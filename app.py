import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename
import json
import re
from functools import wraps


def clean_description(text):
    """Clean description text by removing excessive line breaks and formatting"""
    if not text:
        return text
    
    # Replace multiple consecutive line breaks with maximum of 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production
# მაქსიმალური ატვირთვის ზომა (მაგ: 500MB)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

PROJECTS_DIR = 'projects'
PROJECTS_JSON = 'projects.json'
COMMENTS_JSON = 'comments.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'html', 'docx', 'txt', 'mp4', 'webm', 'ogg', 'mov', 'avi'}
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # Change this in production

# Helpers

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_projects():
    if os.path.exists(PROJECTS_JSON):
        with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_projects(projects):
    with open(PROJECTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

def load_comments():
    if os.path.exists(COMMENTS_JSON):
        with open(COMMENTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_comments(comments):
    with open(COMMENTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes

@app.route('/admin/edit/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return 'Project not found', 404
    project_path = os.path.join(PROJECTS_DIR, project_id)
    description_path = os.path.join(project_path, 'description.txt')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        viewer3d = request.form['viewer3d']
        loading_video = request.form.get('loading_video', '')
        loading_audio = request.form.get('loading_audio', '')
        files = request.files.getlist('files')
        # მთავარი ფოტოს არჩევა
        selected_main_image = request.form.get('main_image_select')
        # Handle existing images and their captions
        other_images = []
        idx = 0
        while True:
            file_key = f'existing_file_{idx}'
            caption_key = f'caption_existing_{idx}'
            if file_key in request.form:
                file_name = request.form[file_key]
                caption = request.form.get(caption_key, '')
                other_images.append({"file": file_name, "caption": caption})
                idx += 1
            else:
                break
        # Handle new uploads
        img_idx = 0
        new_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_path, filename))
                caption = request.form.get(f'caption_{img_idx}', '')
                new_files.append(filename)
                other_images.append({"file": filename, "caption": caption})
                img_idx += 1
        # Update description
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(description)
        # Update project object
        project['title'] = title
        # თუ აირჩია მთავარი ფოტო, დავაყენოთ
        if selected_main_image:
            project['main_image'] = selected_main_image
        elif new_files:
            project['main_image'] = new_files[0]
        # თუ არცერთი, ძველი არ იცვლება
        project['other_images'] = other_images
        project['viewer3D'] = viewer3d
        project['loading_video'] = loading_video
        project['loading_audio'] = loading_audio
        project['latitude'] = request.form.get('latitude', '').strip()
        project['longitude'] = request.form.get('longitude', '').strip()
        
        # Dynamic project info
        project_info = {}
        i = 0
        while True:
            key = request.form.get(f'info_key_{i}', '').strip()
            value = request.form.get(f'info_value_{i}', '').strip()
            if key and value:
                project_info[key] = value
            elif not key:
                break
            i += 1
        project['project_info'] = project_info
        
        # Categories processing
        type_categories = request.form.getlist('type_categories')
        period_categories = request.form.getlist('period_categories')
        project['type_categories'] = type_categories
        project['period_categories'] = period_categories
        
        save_projects(projects)
        return redirect(url_for('admin_panel'))
    # Read description
    description = ''
    if os.path.exists(description_path):
        with open(description_path, 'r', encoding='utf-8') as f:
            description = clean_description(f.read())
    return render_template('edit_project.html', project=project, description=description)

@app.route('/')
def index():
    q = request.args.get('q', '').lower()
    projects = load_projects()
    if q:
        projects = [p for p in projects if q in p['title'].lower()]
    return render_template('index.html', projects=projects, q=q)

@app.route('/project/<project_id>')
def project_detail(project_id):
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return 'Project not found', 404
    
    # Load and normalize comments
    raw_comments = load_comments().get(project_id, [])
    comments = []
    for comment in raw_comments:
        if isinstance(comment, str):
            # Convert old string format to new object format
            comments.append({
                'text': comment,
                'media': None,
                'date': 'ძველი კომენტარი',
                'replies': []
            })
        elif isinstance(comment, dict):
            # Ensure all required fields exist
            if 'replies' not in comment:
                comment['replies'] = []
            if 'date' not in comment:
                comment['date'] = 'ძველი კომენტარი'
            comments.append(comment)
    
    # Read description.txt
    description = ''
    desc_path = os.path.join('projects', project['folder'], 'description.txt')
    if os.path.exists(desc_path):
        with open(desc_path, 'r', encoding='utf-8') as f:
            description = clean_description(f.read())
    return render_template('project_detail.html', project=project, comments=comments, description=description)

@app.route('/add_comment/<project_id>', methods=['POST'])
def add_comment(project_id):
    print(f"Add comment called for project {project_id}")
    print(f"Request form data: {dict(request.form)}")
    print(f"Request files: {dict(request.files)}")
    
    comments = load_comments()
    comment_text = request.form.get('comment', '').strip()
    parent_id = request.form.get('parent_id', '').strip()
    media_file = request.files.get('media')
    
    if comment_text or media_file:
        # Handle media file upload
        media_filename = None
        if media_file and media_file.filename and allowed_file(media_file.filename):
            project_path = os.path.join(PROJECTS_DIR, project_id, 'comments')
            os.makedirs(project_path, exist_ok=True)
            media_filename = secure_filename(media_file.filename)
            media_file.save(os.path.join(project_path, media_filename))
        
        # Create comment object
        comment_obj = {
            'text': comment_text,
            'media': media_filename,
            'date': 'ახლახანს',
            'replies': []
        }
        
        # Initialize project comments if not exists
        if project_id not in comments:
            comments[project_id] = []
        
        # Add as reply or new comment
        if parent_id and parent_id.isdigit():
            parent_idx = int(parent_id)
            if parent_idx < len(comments[project_id]):
                # Ensure parent comment has proper structure
                if isinstance(comments[project_id][parent_idx], str):
                    comments[project_id][parent_idx] = {
                        'text': comments[project_id][parent_idx],
                        'media': None,
                        'date': 'ძველი კომენტარი',
                        'replies': []
                    }
                if 'replies' not in comments[project_id][parent_idx]:
                    comments[project_id][parent_idx]['replies'] = []
                comments[project_id][parent_idx]['replies'].append(comment_obj)
        else:
            comments[project_id].append(comment_obj)
        
        save_comments(comments)
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/admin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    projects = load_projects()
    return render_template('admin_panel.html', projects=projects)

@app.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def upload_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        viewer3d = request.form['viewer3d']
        loading_video = request.form.get('loading_video', '')
        loading_audio = request.form.get('loading_audio', '')
        files = request.files.getlist('files')
        project_id = secure_filename(title.lower().replace(' ', '_'))
        if not project_id:
            project_id = 'project_' + str(len(load_projects()) + 1)
        project_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_path, exist_ok=True)
        main_image = None
        other_images = []
        img_idx = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_path, filename))
                caption = request.form.get(f'caption_{img_idx}', '')
                if not main_image and filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                    main_image = filename
                else:
                    other_images.append({"file": filename, "caption": caption})
                img_idx += 1
        # Save description
        with open(os.path.join(project_path, 'description.txt'), 'w', encoding='utf-8') as f:
            f.write(description)
        # Update projects.json
        projects = load_projects()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        
        # Dynamic project info
        project_info = {}
        i = 0
        while True:
            key = request.form.get(f'info_key_{i}', '').strip()
            value = request.form.get(f'info_value_{i}', '').strip()
            if key and value:
                project_info[key] = value
            elif not key:
                break
            i += 1
        
        # Categories processing
        type_categories = request.form.getlist('type_categories')
        period_categories = request.form.getlist('period_categories')
        
        project_obj = {
            'id': project_id,
            'title': title,
            'main_image': main_image,
            'other_images': other_images,
            'viewer3D': viewer3d,
            'loading_video': loading_video,
            'loading_audio': loading_audio,
            'description_file': 'description.txt',
            'folder': project_id,
            'latitude': latitude,
            'longitude': longitude,
            'project_info': project_info,
            'type_categories': type_categories,
            'period_categories': period_categories
        }
        projects.append(project_obj)
        save_projects(projects)
        return redirect(url_for('admin_panel'))
    return render_template('upload.html')

@app.route('/admin/delete/<project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    # Remove project folder and update projects.json
    project_path = os.path.join(PROJECTS_DIR, project_id)
    if os.path.exists(project_path):
        for root, dirs, files in os.walk(project_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(project_path)
    projects = load_projects()
    projects = [p for p in projects if p['id'] != project_id]
    save_projects(projects)
    return redirect(url_for('admin_panel'))

@app.route('/projects/<project_id>/<filename>')
def project_file(project_id, filename):
    return send_from_directory(os.path.join(PROJECTS_DIR, project_id), filename)

@app.route('/projects/<project_id>/comments/<filename>')
def comment_media(project_id, filename):
    return send_from_directory(os.path.join(PROJECTS_DIR, project_id, 'comments'), filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# --- LIVE SEARCH ROUTE ---
@app.route('/live_search')
def live_search():
    q = request.args.get('q', '').lower()
    projects = load_projects()
    if q:
        filtered = [p for p in projects if q in p['title'].lower()]
    else:
        filtered = projects
    # Only send minimal fields needed for card rendering
    result = [
        {
            'id': p['id'],
            'title': p['title'],
            'main_image': p.get('main_image', ''),
            'folder': p.get('folder', p['id']),
            'type_categories': p.get('type_categories', []),
            'period_categories': p.get('period_categories', [])
        }
        for p in filtered
    ]
    return jsonify({'projects': result})

if __name__ == '__main__':
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    # For production (Render.com), use environment variables
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
