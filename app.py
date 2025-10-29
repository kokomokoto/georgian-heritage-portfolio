import os
import time
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail, Message
import cloudinary
import cloudinary.uploader
import cloudinary.api
import json
import re
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME') or 'localhost:5001'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'

# Import models after app creation
from models import db, User, Comment, Like
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'გთხოვთ შეხვიდეთ ანგარიშში.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

PROJECTS_DIR = 'projects'
PROJECTS_JSON = 'projects.json'
COMMENTS_JSON = 'comments.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'html', 'docx', 'txt', 'mp4', 'webm', 'ogg', 'mov', 'avi'}
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # Change this in production

# Helpers

def send_email(subject, recipient, template, **kwargs):
    """Send email using Flask-Mail"""
    try:
        # For development: print email content to console instead of sending
        if app.config.get('MAIL_USERNAME') == 'your_email@gmail.com':
            print(f"\n=== EMAIL DEBUG (Development Mode) ===")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            if 'reset_url' in kwargs:
                print(f"Reset URL: {kwargs['reset_url']}")
            if 'verification_url' in kwargs:
                print(f"Verification URL: {kwargs['verification_url']}")
            print("=== END EMAIL DEBUG ===\n")
            return True
        
        # Production email sending
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=render_template(template, **kwargs),
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_verification_email(user):
    """Send email verification"""
    token = user.generate_verification_token()
    db.session.commit()
    
    verification_url = url_for('verify_email', token=token, _external=True)
    return send_email(
        subject='ელ.ფოსტის დადასტურება - ქართული მემკვიდრეობა',
        recipient=user.email,
        template='email/verify_email.html',
        user=user,
        verification_url=verification_url
    )

def send_password_reset_email(user):
    """Send password reset email"""
    token = user.generate_reset_token()
    db.session.commit()
    
    reset_url = url_for('reset_password', token=token, _external=True)
    return send_email(
        subject='პაროლის აღდგენა - ქართული მემკვიდრეობა',
        recipient=user.email,
        template='email/reset_password.html',
        user=user,
        reset_url=reset_url
    )

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
            return redirect(url_for('admin_login', next=request.url))
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
        
        # Handle all images from the unified system
        all_images = []
        main_image_url = None
        selected_main = request.form.get('main_image_selector', '')
        
        # Collect all images (main + others)
        # Check for main image
        main_url = request.form.get('all_image_url_main', '').strip()
        main_caption = request.form.get('all_image_caption_main', '').strip()
        if main_url:
            all_images.append({
                'url': main_url,
                'caption': main_caption,
                'index': 'main'
            })
            if selected_main == 'main':
                main_image_url = main_url
        
        # Check for other images
        i = 0
        while True:
            image_url = request.form.get(f'all_image_url_{i}', '').strip()
            image_caption = request.form.get(f'all_image_caption_{i}', '').strip()
            if image_url:
                all_images.append({
                    'url': image_url,
                    'caption': image_caption,
                    'index': str(i)
                })
                if selected_main == str(i):
                    main_image_url = image_url
            elif i == 0:
                pass  # Check at least the first one
            else:
                break
            i += 1
        
        # If no main image selected, use first image
        if not main_image_url and all_images:
            main_image_url = all_images[0]['url']
        
        # Create other_images array (exclude the main image)
        other_images = []
        for img in all_images:
            if img['url'] != main_image_url:
                other_images.append({
                    'url': img['url'],
                    'caption': img['caption']
                })
        
        # Handle document files (docx, html) if any
        files = request.files.getlist('files')
        documents = project.get('documents', [])  # Keep existing documents
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_path, filename))
                if filename not in documents:
                    documents.append(filename)
        
        # Update description
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(description)
        
        # Update project object
        project['title'] = title
        project['main_image'] = main_image_url
        project['other_images'] = other_images
        project['documents'] = documents
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

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('ეს ელ. ფოსტა უკვე რეგისტრირებულია.', 'error')
            return render_template('auth/register.html', form=form)
        
        try:
            user = User(
                name=form.name.data,
                email=form.email.data,
                email_verified=True  # Skip email verification for development
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            if send_verification_email(user):
                flash('რეგისტრაცია წარმატებით დასრულდა! გთხოვთ შეამოწმოთ ელ. ფოსტა ვერიფიკაციისთვის.', 'success')
            else:
                flash('რეგისტრაცია წარმატებით დასრულდა, მაგრამ ვერიფიკაციის ელ. ფოსტა ვერ გაიგზავნა.', 'warning')
            
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('რეგისტრაციის შეცდომა. სცადეთ თავიდან.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try email
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('წარმატებით შეხვედით!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('არასწორი ელ. ფოსტა ან პაროლი.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('თქვენ გახვედით ანგარიშიდან.', 'info')
    return redirect(url_for('index'))

@app.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        flash('ელ. ფოსტა წარმატებით დადასტურდა! ახლა შეგიძლიათ შეხვიდეთ.', 'success')
        return redirect(url_for('login'))
    else:
        flash('არასწორი ან ვადაგასული ვერიფიკაციის ლინკი.', 'error')
        return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if send_password_reset_email(user):
                flash('პაროლის აღდგენის ლინკი გაიგზავნა თქვენს ელ. ფოსტაზე.', 'success')
            else:
                flash('ელ. ფოსტის გაგზავნისას მოხდა შეცდომა.', 'error')
        else:
            # Security: Don't reveal if email exists
            flash('თუ ეს ელ. ფოსტა რეგისტრირებულია, მიიღებთ აღდგენის ლინკს.', 'info')
        return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('არასწორი ან ვადაგასული აღდგენის ლინკი.', 'error')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash('პაროლი წარმატებით შეიცვალა! ახლა შეგიძლიათ შეხვიდეთ.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', form=form)

@app.route('/resend_verification')
@login_required
def resend_verification():
    if current_user.email_verified:
        flash('ელ. ფოსტა უკვე დადასტურებულია.', 'info')
        return redirect(url_for('index'))
    
    if send_verification_email(current_user):
        flash('ვერიფიკაციის ლინკი თავიდან გაიგზავნა.', 'success')
    else:
        flash('ელ. ფოსტის გაგზავნისას მოხდა შეცდომა.', 'error')
    
    return redirect(url_for('index'))

@app.route('/project/<project_id>')
def project_detail(project_id):
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return 'Project not found', 404
    
    # Load comments from database - pass Comment objects directly to template
    comments = Comment.query.filter_by(project_id=project_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Read description.txt
    description = ''
    desc_path = os.path.join('projects', project['folder'], 'description.txt')
    if os.path.exists(desc_path):
        with open(desc_path, 'r', encoding='utf-8') as f:
            description = clean_description(f.read())
    return render_template('project_detail.html', project=project, comments=comments, description=description)

@app.route('/test-comment')
def test_comment():
    print(f"Current user: {current_user}")
    print(f"Is authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        print(f"User name: {current_user.name}, Email: {current_user.email}")
    return render_template('test_comment.html')

@app.route('/add_comment/<project_id>', methods=['POST'])
@login_required
def add_comment(project_id):
    # Check if user's email is verified
    if not current_user.email_verified:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'გთხოვთ დაადასტუროთ ელ. ფოსტა კომენტარის დასაწერად.'})
        flash('გთხოვთ დაადასტუროთ ელ. ფოსტა კომენტარის დასაწერად.', 'error')
        return redirect(url_for('project_detail', project_id=project_id))
    
    print(f"Add comment called for project {project_id}")
    print(f"Request form data: {dict(request.form)}")
    print(f"Request files: {dict(request.files)}")
    
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    comment_text = request.form.get('comment', '').strip()
    parent_id = request.form.get('parent_id', '').strip()
    media_file = request.files.get('media')
    
    if comment_text or media_file:
        # Handle media file upload to Cloudinary
        media_url = None
        if media_file and media_file.filename and allowed_file(media_file.filename):
            try:
                upload_result = cloudinary.uploader.upload(
                    media_file,
                    folder="comments",
                    public_id=f"comment_{int(time.time())}_{secure_filename(media_file.filename)}"
                )
                media_url = upload_result['secure_url']
            except Exception as e:
                print(f"Failed to upload to Cloudinary: {e}")
                # Fallback to local storage
                project_path = os.path.join(PROJECTS_DIR, project_id, 'comments')
                os.makedirs(project_path, exist_ok=True)
                media_filename = secure_filename(media_file.filename)
                media_file.save(os.path.join(project_path, media_filename))
                media_url = f"/projects/{project_id}/comments/{media_filename}"
        
        # Create comment in database
        if parent_id and parent_id.isdigit():
            # Reply to existing comment
            new_comment = Comment(
                content=comment_text,
                project_id=project_id,
                user_id=current_user.id,
                parent_id=int(parent_id),
                media_url=media_url
            )
        else:
            # New top-level comment
            new_comment = Comment(
                content=comment_text,
                project_id=project_id,
                user_id=current_user.id,
                media_url=media_url
            )
        
        db.session.add(new_comment)
        db.session.commit()
        
        if is_ajax:
            # Return comment data as JSON
            comment_data = {
                'success': True,
                'comment': {
                    'id': new_comment.id,
                    'content': new_comment.content,
                    'author': {
                        'name': new_comment.author.name if new_comment.author else 'Unknown',
                        'id': new_comment.author.id if new_comment.author else 0
                    },
                    'media_url': new_comment.media_url,
                    'parent_id': new_comment.parent_id,
                    'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
            }
            return jsonify(comment_data)
        
        flash('კომენტარი წარმატებით დაემატა!', 'success')
    
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/toggle_like/<int:comment_id>', methods=['POST'])
@login_required
def toggle_like(comment_id):
    # Check if user's email is verified
    if not current_user.email_verified:
        return jsonify({'success': False, 'error': 'გთხოვთ დაადასტუროთ ელ. ფოსტა ლაიქისთვის.'})
    
    comment = Comment.query.get_or_404(comment_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    
    if existing_like:
        # Unlike - remove the like
        db.session.delete(existing_like)
        db.session.commit()
        is_liked = False
        message = 'ლაიქი მოიშალა'
    else:
        # Like - add new like
        new_like = Like(user_id=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
        db.session.commit()
        is_liked = True
        message = 'ლაიქი დაემატა'
    
    # Get updated like count
    like_count = Like.query.filter_by(comment_id=comment_id).count()
    
    return jsonify({
        'success': True,
        'is_liked': is_liked,
        'like_count': like_count,
        'message': message
    })

@app.route('/delete_comment/<int:comment_id>/<project_id>', methods=['POST'])
@login_required
def delete_comment(comment_id, project_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user can delete this comment
    can_delete = False
    
    # Check if it's the comment author
    if comment.user_id == current_user.id:
        can_delete = True
    
    # Check if it's an admin user (if you have admin functionality)
    # if hasattr(current_user, 'is_admin') and current_user.is_admin:
    #     can_delete = True
    
    if not can_delete:
        flash('თქვენ არ გაქვთ ამ კომენტარის წაშლის უფლება.', 'error')
        return redirect(url_for('project_detail', project_id=project_id))
    
    try:
        # Delete all nested replies first
        def delete_replies(comment):
            for reply in comment.replies:
                delete_replies(reply)  # Recursively delete nested replies
                db.session.delete(reply)
        
        delete_replies(comment)
        db.session.delete(comment)
        db.session.commit()
        flash('კომენტარი წარმატებით წაიშალა!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('კომენტარის წაშლისას დაფიქსირდა შეცდომა.', 'error')
        print(f"Error deleting comment: {e}")
    
    return redirect(url_for('project_detail', project_id=project_id))
    
    # Check if it's a registered user's own comment
    if current_user.is_authenticated and comment.user_id == current_user.id:
        can_delete = True
    
    if not can_delete:
        flash('თქვენ არ გაქვთ ამ კომენტარის წაშლის უფლება.', 'error')
        return redirect(url_for('project_detail', project_id=project_id))
    
    try:
        # Delete all replies to this comment first
        Comment.query.filter_by(parent_id=comment_id).delete()
        
        # Delete the comment itself
        db.session.delete(comment)
        db.session.commit()
        flash('კომენტარი წარმატებით წაიშალა!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('კომენტარის წაშლისას შეცდომა მოხდა.', 'error')
        print(f"Error deleting comment: {e}")
    
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
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
        
        # Handle all images from the unified system
        all_images = []
        main_image_url = None
        selected_main = request.form.get('main_image_selector', '0')  # Default to first image
        
        # Collect all images
        i = 0
        while True:
            image_url = request.form.get(f'all_image_url_{i}', '').strip()
            image_caption = request.form.get(f'all_image_caption_{i}', '').strip()
            if image_url:
                all_images.append({
                    'url': image_url,
                    'caption': image_caption,
                    'index': str(i)
                })
                if selected_main == str(i):
                    main_image_url = image_url
            elif i == 0:
                pass  # Check at least the first one
            else:
                break
            i += 1
        
        # If no main image selected, use first image
        if not main_image_url and all_images:
            main_image_url = all_images[0]['url']
        
        # Create other_images array (exclude the main image)
        other_images = []
        for img in all_images:
            if img['url'] != main_image_url:
                other_images.append({
                    'url': img['url'],
                    'caption': img['caption']
                })
        
        project_id = secure_filename(title.lower().replace(' ', '_'))
        if not project_id:
            project_id = 'project_' + str(len(load_projects()) + 1)
        
        project_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(project_path, exist_ok=True)
        
        # Handle document files (docx, html) if any
        files = request.files.getlist('files')
        documents = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_path, filename))
                documents.append(filename)
        
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
            'main_image': main_image_url,  # Now URL instead of filename
            'other_images': other_images,  # Now contains URLs with captions
            'documents': documents,  # Separate array for document files
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
