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

# Session configuration for better persistence
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Remove SERVER_NAME for now as it can cause session issues
# Only set SERVER_NAME for local development
# if os.environ.get('FLASK_ENV') != 'production':
#     app.config['SERVER_NAME'] = 'localhost:5001'
#     app.config['PREFERRED_URL_SCHEME'] = 'http'
# else:
#     # For production (Render), let Flask auto-detect the server name
#     app.config['PREFERRED_URL_SCHEME'] = 'https'

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'

# Import models after app creation
from models import db, User, Comment, Like, Project
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

PROJECTS_DIR = 'projects'
PROJECTS_JSON = 'projects.json'
COMMENTS_JSON = 'comments.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'ogg', 'mov', 'avi'}
ADMIN_USERNAME = 'შენი_ადმინი'
ADMIN_PASSWORD = 'შენი_ძლიერი_პაროლი_2024'  # შეცვალე production-ში

# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("✅ Database initialized successfully")
        
        # Seed database with initial projects if empty
        if Project.query.count() == 0:
            try:
                with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
                    projects_data = json.load(f)
                for proj_data in projects_data:
                    description = ""
                    if proj_data.get('description_file'):
                        desc_path = os.path.join(PROJECTS_DIR, proj_data['folder'], proj_data['description_file'])
                        if os.path.exists(desc_path):
                            with open(desc_path, 'r', encoding='utf-8') as df:
                                description = df.read()
                    project = Project(
                        id=proj_data['id'],
                        title=proj_data['title'],
                        main_image=proj_data.get('main_image'),
                        other_images=json.dumps(proj_data.get('other_images', [])),
                        viewer3D=proj_data.get('viewer3D'),
                        description=description,
                        description_file=proj_data.get('description_file'),
                        folder=proj_data.get('folder'),
                        latitude=proj_data.get('latitude'),
                        longitude=proj_data.get('longitude'),
                        documents=json.dumps(proj_data.get('documents', [])),
                        loading_video=proj_data.get('loading_video'),
                        loading_audio=proj_data.get('loading_audio'),
                        project_info=json.dumps(proj_data.get('project_info', {})),
                        type_categories=json.dumps(proj_data.get('type_categories', [])),
                        period_categories=json.dumps(proj_data.get('period_categories', [])),
                    )
                    db.session.add(project)
                db.session.commit()
                print("✅ Seeded database with initial projects")
            except Exception as e:
                print(f"⚠️ Could not seed database: {e}")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        # Continue anyway - don't crash the app

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
    """Load projects from database"""
    try:
        projects = Project.query.all()
        result = []
        for project in projects:
            # Load description from file if not in database
            description = project.description
            if not description and project.description_file:
                desc_path = os.path.join('projects', project.folder, 'description.txt')
                if os.path.exists(desc_path):
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        description = clean_description(f.read())
            
            result.append({
                'id': project.id,
                'title': project.title,
                'main_image': project.main_image,
                'main_image_caption': project.main_image_caption,
                'other_images': json.loads(project.other_images) if project.other_images else [],
                'viewer3D': project.viewer3D,
                'description': description,
                'description_file': project.description_file,
                'folder': project.folder,
                'latitude': project.latitude,
                'longitude': project.longitude,
                'documents': json.loads(project.documents) if project.documents else [],
                'loading_video': project.loading_video,
                'loading_audio': project.loading_audio,
                'project_info': json.loads(project.project_info) if project.project_info else {},
                'type_categories': json.loads(project.type_categories) if project.type_categories else [],
                'period_categories': json.loads(project.period_categories) if project.period_categories else []
            })
        return result
    except Exception as e:
        print(f"Error loading projects from database: {e}")
        # Fallback to JSON if database fails
        if os.path.exists(PROJECTS_JSON):
            with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def save_projects(projects):
    """Save projects to database"""
    try:
        # Clear existing projects
        Project.query.delete()

        # Add new projects
        for project_data in projects:
            project = Project(
                id=project_data['id'],
                title=project_data['title'],
                main_image=project_data.get('main_image'),
                main_image_caption=project_data.get('main_image_caption'),
                other_images=json.dumps(project_data.get('other_images', [])),
                viewer3D=project_data.get('viewer3D'),
                description=project_data.get('description'),
                description_file=project_data.get('description_file'),
                folder=project_data.get('folder'),
                latitude=project_data.get('latitude'),
                longitude=project_data.get('longitude'),
                documents=json.dumps(project_data.get('documents', [])),
                loading_video=project_data.get('loading_video'),
                loading_audio=project_data.get('loading_audio'),
                project_info=json.dumps(project_data.get('project_info', {})),
                type_categories=json.dumps(project_data.get('type_categories', [])),
                period_categories=json.dumps(project_data.get('period_categories', []))
            )
            db.session.add(project)

        db.session.commit()
        print(f"✅ Saved {len(projects)} projects to database")
    except Exception as e:
        print(f"❌ Error saving projects to database: {e}")
        # Fallback to JSON
        try:
            with open(PROJECTS_JSON, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            print("💾 Saved to JSON as fallback")
        except Exception as json_error:
            print(f"❌ Failed to save to JSON: {json_error}")

def load_comments():
    if os.path.exists(COMMENTS_JSON):
        with open(COMMENTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_comments(comments):
    with open(COMMENTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes

@app.route('/admin/edit/<project_id>', methods=['GET', 'POST'])
@admin_required
def edit_project(project_id):
    # Get project from database
    project_db = Project.query.get(project_id)
    if not project_db:
        flash('პროექტი ვერ მოიძებნა.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Convert to dict for template compatibility
    project = {
        'id': project_db.id,
        'title': project_db.title,
        'main_image': project_db.main_image,
        'main_image_caption': project_db.main_image_caption,
        'other_images': json.loads(project_db.other_images) if project_db.other_images else [],
        'viewer3D': project_db.viewer3D,
        'description': project_db.description,
        'description_file': project_db.description_file,
        'folder': project_db.folder,
        'latitude': project_db.latitude,
        'longitude': project_db.longitude,
        'documents': json.loads(project_db.documents) if project_db.documents else [],
        'loading_video': project_db.loading_video,
        'loading_audio': project_db.loading_audio,
        'project_info': json.loads(project_db.project_info) if project_db.project_info else {},
        'type_categories': json.loads(project_db.type_categories) if project_db.type_categories else [],
        'period_categories': json.loads(project_db.period_categories) if project_db.period_categories else []
    }
    
    if request.method == 'POST':
        # Get form data - only title is required
        title = request.form.get('title', '').strip()
        if not title:
            flash('სათაური სავალდებულოა.', 'error')
            return render_template('edit_project.html', project=project, description=project['description'])
        
        # Handle all images from the unified system
        all_images = []
        main_image_url = None
        selected_main = request.form.get('main_image_selector', 'main')  # Default to main image
        
        # Handle main image separately
        main_image_url_input = request.form.get('all_image_url_main', '').strip()
        main_image_caption_input = request.form.get('all_image_caption_main', '').strip()
        if main_image_url_input:
            all_images.append({
                'url': main_image_url_input,
                'caption': main_image_caption_input,
                'index': 'main'
            })
            if selected_main == 'main':
                main_image_url = main_image_url_input
        
        # Collect all other images
        i = 0
        empty_count = 0
        while empty_count < 3:  # Continue until we find 3 consecutive empty image fields
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
                empty_count = 0  # Reset empty count when we find a valid image
            else:
                empty_count += 1
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
        
        # Update project data in database
        project_db.title = title
        project_db.main_image = main_image_url
        project_db.main_image_caption = main_image_caption_input if main_image_caption_input else None
        project_db.other_images = json.dumps(other_images) if other_images else None
        
        # Save optional fields only if provided
        desc = request.form.get('description', '').strip()
        if desc:
            project_db.description = desc
        
        viewer3d = request.form.get('viewer3d', '').strip()
        if viewer3d:
            project_db.viewer3D = viewer3d
            
        # Save coordinates
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        if latitude:
            project_db.latitude = latitude
        if longitude:
            project_db.longitude = longitude
            
        # Save loading media
        loading_video = request.form.get('loading_video', '').strip()
        loading_audio = request.form.get('loading_audio', '').strip()
        if loading_video:
            project_db.loading_video = loading_video
        if loading_audio:
            project_db.loading_audio = loading_audio
            
        # Save project info
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
        if project_info:
            project_db.project_info = json.dumps(project_info)
            
        # Save categories
        type_categories = request.form.getlist('type_categories')
        period_categories = request.form.getlist('period_categories')
        if type_categories:
            project_db.type_categories = json.dumps(type_categories)
        if period_categories:
            project_db.period_categories = json.dumps(period_categories)
            
        # Commit changes
        db.session.commit()
        flash('პროექტი წარმატებით განახლდა!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('edit_project.html', project=project, description=project['description'])

@app.route('/')
def index():
    try:
        q = request.args.get('q', '').lower()
        projects = load_projects()
        if q:
            projects = [p for p in projects if q in p['title'].lower()]
        return render_template('index.html', projects=projects, q=q)
    except Exception as e:
        # For debugging on Render
        return f"Error in index route: {str(e)}", 500

@app.route('/debug')
def debug():
    """Debug route to check what's happening on Render"""
    import os
    debug_info = {
        'cwd': os.getcwd(),
        'projects_dir_exists': os.path.exists(PROJECTS_DIR),
        'projects_json_exists': os.path.exists(PROJECTS_JSON),
        'templates_exist': os.path.exists('templates'),
        'index_template_exists': os.path.exists('templates/index.html'),
    }
    return f"Debug info: {debug_info}"

@app.route('/admin/users')
def admin_users():
    """Admin panel to view registered users"""
    # Simple password protection
    password = request.args.get('password')
    if password != 'შენი_ძლიერი_პაროლი_2024':  # Change this password!
        return "Access denied. Add ?password=admin123 to URL", 403
    
    users = User.query.all()
    
    users_info = []
    for user in users:
        users_info.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'verified': user.email_verified,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'
        })
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin - Users</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .verified { color: green; }
            .not-verified { color: red; }
        </style>
    </head>
    <body>
        <h1>დარეგისტრირებული მომხმარებლები</h1>
        <p>სულ: {} მომხმარებელი</p>
        <table>
            <tr>
                <th>ID</th>
                <th>სახელი</th>
                <th>Email</th>
                <th>ვერიფიცირებული</th>
                <th>რეგისტრაციის თარიღი</th>
            </tr>
    """.format(len(users_info))
    
    for user in users_info:
        verified_class = "verified" if user['verified'] else "not-verified"
        verified_text = "კი ✓" if user['verified'] else "არა ✗"
        
        html += f"""
            <tr>
                <td>{user['id']}</td>
                <td>{user['name']}</td>
                <td>{user['email']}</td>
                <td class="{verified_class}">{verified_text}</td>
                <td>{user['created_at']}</td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <a href="/">← მთავარ გვერდზე დაბრუნება</a>
    </body>
    </html>
    """
    
    return html

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
    
    # Read description.txt or use from database
    description = project.get('description', '')
    if not description:
        desc_path = os.path.join('projects', project['folder'], 'description.txt')
        if os.path.exists(desc_path):
            with open(desc_path, 'r', encoding='utf-8') as f:
                description = clean_description(f.read())
    else:
        description = clean_description(description)
    return render_template('project_detail.html', project=project, comments=comments, description=description)

@app.route('/debug/project/<project_id>')
def debug_project_detail(project_id):
    """Debug version of project detail to test comments and images"""
    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return 'Project not found', 404
    
    # Load comments from database
    comments = Comment.query.filter_by(project_id=project_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    return render_template('debug_comments.html', project=project, comments=comments)

@app.route('/test-modal')
def test_modal():
    """Serve simple modal test page"""
    return send_from_directory('.', 'test_modal_simple.html')

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
    print("\n" + "="*50)
    print("ADD_COMMENT FUNCTION CALLED!")
    print(f"Project ID: {project_id}")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print("="*50)
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
    media_files = request.files.getlist('media')  # Get multiple files
    
    print(f"Parsed - comment_text: '{comment_text}', parent_id: '{parent_id}', media_files count: {len(media_files)}")
    for i, media_file in enumerate(media_files):
        print(f"Media file {i}: filename={media_file.filename if media_file else None}, content_type={media_file.content_type if media_file else None}")
    
    if comment_text or (media_files and any(f.filename for f in media_files)):
        print("Processing comment or media...")
        # Handle multiple media files upload to Cloudinary
        media_urls = []
        if media_files:
            for i, media_file in enumerate(media_files):
                if media_file and media_file.filename and allowed_file(media_file.filename):
                    print(f"Uploading file {i+1}/{len(media_files)} to Cloudinary: {media_file.filename}")
                    
                    # Determine file type
                    file_extension = media_file.filename.rsplit('.', 1)[1].lower()
                    is_video = file_extension in {'mp4', 'webm', 'ogg', 'mov', 'avi'}
                    
                    try:
                        upload_params = {
                            "folder": "comments",
                            "public_id": f"comment_{int(time.time())}_{i}_{secure_filename(media_file.filename)}"
                        }
                        
                        # Add resource_type for videos
                        if is_video:
                            upload_params["resource_type"] = "video"
                        
                        upload_result = cloudinary.uploader.upload(media_file, **upload_params)
                        media_urls.append(upload_result['secure_url'])
                        print(f"Cloudinary upload successful for file {i+1}: {upload_result['secure_url']}")
                        print(f"File type: {'Video' if is_video else 'Image'}")
                        
                    except Exception as e:
                        print(f"Failed to upload file {i+1} to Cloudinary: {e}")
                        print(f"Error details: {type(e).__name__}")
                        print(f"CRITICAL: Using local fallback - files will be deleted on Render restart!")
                        
                        # On production (Render), this is a MAJOR PROBLEM
                        if os.environ.get('DATABASE_URL'):  # Production check
                            print("ERROR: Local storage on Render.com will lose files!")
                            print("Environment check - Cloudinary credentials:")
                            print(f"  CLOUD_NAME: {'SET' if os.environ.get('CLOUDINARY_CLOUD_NAME') else 'MISSING'}")
                            print(f"  API_KEY: {'SET' if os.environ.get('CLOUDINARY_API_KEY') else 'MISSING'}")
                            print(f"  API_SECRET: {'SET' if os.environ.get('CLOUDINARY_API_SECRET') else 'MISSING'}")
                        
                        # Fallback to local storage (TEMPORARY for production)
                        project_path = os.path.join(PROJECTS_DIR, project_id, 'comments')
                        os.makedirs(project_path, exist_ok=True)
                        media_filename = secure_filename(media_file.filename)
                        media_file.save(os.path.join(project_path, media_filename))
                        local_url = f"/projects/{project_id}/comments/{media_filename}"
                        media_urls.append(local_url)
                        print(f"Local storage fallback for file {i+1}: {local_url}")
                        print(f"WARNING: This file will be deleted on server restart!")
                else:
                    if media_file and media_file.filename:
                        print(f"File {i+1} not allowed: {media_file.filename}")
                        print(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
                    else:
                        print(f"No valid media file {i+1} to upload. media_file={media_file}, filename={media_file.filename if media_file else None}")
        
        print(f"Final media_urls: {media_urls}")
        
        # Create comment in database
        if parent_id and parent_id.isdigit():
            # Reply to existing comment
            print(f"Creating reply comment with parent_id: {parent_id}")
            new_comment = Comment(
                content=comment_text,
                project_id=project_id,
                user_id=current_user.id,
                parent_id=int(parent_id)
            )
        else:
            # New top-level comment
            print("Creating top-level comment")
            new_comment = Comment(
                content=comment_text,
                project_id=project_id,
                user_id=current_user.id
            )
        
        # Set multiple media URLs
        new_comment.set_media_urls(media_urls)
        
        print(f"Saving comment to database: content='{new_comment.content}', media_urls='{new_comment.media_urls}'")
        db.session.add(new_comment)
        db.session.commit()
        print(f"Comment saved with ID: {new_comment.id}")
        
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
                    'media_urls': new_comment.get_media_urls(),  # Return array of URLs
                    'parent_id': new_comment.parent_id,
                    'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
            }
            print(f"Returning AJAX response: {comment_data}")
            return jsonify(comment_data)
        
        flash('კომენტარი წარმატებით დაემატა!', 'success')
    else:
        print("No comment text or media file provided")
    
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
def delete_comment(comment_id, project_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user can delete this comment
    can_delete = False
    
    # For registered users - check if it's their comment
    if current_user.is_authenticated and comment.user_id == current_user.id:
        can_delete = True
    
    # For admin users - they can delete any comment
    if session.get('logged_in'):
        can_delete = True
    
    # For email-based deletion - check provided email
    author_email = request.form.get('author_email')
    if author_email and comment.author and comment.author.email == author_email.strip():
        can_delete = True
    
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
    session.clear()  # Clear all session data
    response = redirect(url_for('index'))
    response.delete_cookie('session')  # Delete session cookie
    return response

@app.route('/admin/panel')
@admin_required
def admin_panel():
    projects = load_projects()
    return render_template('admin_panel.html', projects=projects)

@app.route('/debug/database')
def debug_database():
    """Debug endpoint to check database status and backup"""
    
    # Database info
    db_info = {
        'ENVIRONMENT': 'PRODUCTION' if os.environ.get('DATABASE_URL') else 'DEVELOPMENT',
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET (local SQLite)',
        'SQLALCHEMY_DATABASE_URI': app.config['SQLALCHEMY_DATABASE_URI'][:50] + '...' if len(app.config['SQLALCHEMY_DATABASE_URI']) > 50 else app.config['SQLALCHEMY_DATABASE_URI']
    }
    
    # Count records
    try:
        users_count = User.query.count()
        comments_count = Comment.query.count()
        likes_count = Like.query.count()
        
        db_stats = {
            'users': users_count,
            'comments': comments_count,
            'likes': likes_count,
            'total_records': users_count + comments_count + likes_count
        }
    except Exception as e:
        db_stats = {'error': str(e)}
    
    # Recent activity
    try:
        recent_users = User.query.order_by(User.created_at.desc()).limit(3).all()
        recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(3).all()
        
        recent_activity = {
            'recent_users': [{'id': u.id, 'name': u.name, 'email': u.email, 'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else 'N/A'} for u in recent_users],
            'recent_comments': [{'id': c.id, 'content': c.content[:50] + '...' if c.content and len(c.content) > 50 else c.content, 'author': c.author.name if c.author else 'Unknown', 'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else 'N/A'} for c in recent_comments]
        }
    except Exception as e:
        recent_activity = {'error': str(e)}
    
    debug_data = {
        'database_info': db_info,
        'statistics': db_stats,
        'recent_activity': recent_activity,
        'timestamp': time.time()
    }
    
    return jsonify(debug_data)

@app.route('/debug/cloudinary')
def debug_cloudinary():
    """Debug endpoint to check Cloudinary configuration"""
    
    # Check environment variables
    env_info = {
        'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'NOT SET'),
        'CLOUDINARY_API_KEY': 'SET' if os.environ.get('CLOUDINARY_API_KEY') else 'NOT SET',
        'CLOUDINARY_API_SECRET': 'SET' if os.environ.get('CLOUDINARY_API_SECRET') else 'NOT SET',
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET (local SQLite)',
        'ENVIRONMENT': 'PRODUCTION' if os.environ.get('DATABASE_URL') else 'DEVELOPMENT'
    }
    
    # Test Cloudinary connection
    cloudinary_status = 'UNKNOWN'
    cloudinary_error = None
    
    try:
        import cloudinary.api
        result = cloudinary.api.ping()
        cloudinary_status = 'CONNECTED'
        cloudinary_info = result
    except Exception as e:
        cloudinary_status = 'ERROR'
        cloudinary_error = str(e)
        cloudinary_info = None
    
    # Check recent uploads
    recent_uploads = []
    try:
        cloudinary_result = cloudinary.api.resources(
            type="upload",
            prefix="comments/",
            max_results=5
        )
        recent_uploads = cloudinary_result.get('resources', [])
    except Exception as e:
        recent_uploads = [{'error': str(e)}]
    
    debug_data = {
        'environment': env_info,
        'cloudinary_status': cloudinary_status,
        'cloudinary_error': cloudinary_error,
        'cloudinary_info': cloudinary_info,
        'recent_uploads': recent_uploads,
        'timestamp': time.time()
    }
    
    return jsonify(debug_data)

@app.route('/cloud-admin', methods=['GET', 'POST'])
def cloud_admin():
    """Admin panel for viewing cloud database"""
    
    # Simple password protection
    if request.method == 'POST':
        password = request.form.get('password')
        # Change this to your admin password
        if password == 'შენი_ახალი_პაროლი_2024':  # შენი ახალი უსაფრთხო პაროლი!
            session['cloud_admin'] = True
            return redirect(url_for('cloud_admin'))
        else:
            flash('არასწორი პაროლი!', 'error')
    
    # Check if logged in
    if not session.get('cloud_admin'):
        return render_template('cloud_admin_login.html')
    
    # Get all data from cloud database
    try:
        users = User.query.all()
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
        likes = Like.query.all()
        
        # Environment info
        env_info = {
            'database_url': os.environ.get('DATABASE_URL', 'Local SQLite'),
            'cloudinary_cloud': os.environ.get('CLOUDINARY_CLOUD_NAME', 'Not set'),
            'environment': 'PRODUCTION' if os.environ.get('DATABASE_URL') else 'DEVELOPMENT'
        }
        
        return render_template('cloud_admin_panel.html', 
                             users=users, 
                             comments=comments, 
                             likes=likes,
                             env_info=env_info)
                             
    except Exception as e:
        flash(f'Database error: {e}', 'error')
        return render_template('cloud_admin_login.html')

@app.route('/cloud-admin/logout')
def cloud_admin_logout():
    """Logout from cloud admin"""
    session.pop('cloud_admin', None)
    return redirect(url_for('cloud_admin'))

@app.route('/admin/database')
@admin_required
def admin_database():
    """Admin page to view all database contents"""
    try:
        from models import User, Comment, Like
        
        # Get all data from database
        users = User.query.order_by(User.created_at.desc()).all()
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
        likes = Like.query.order_by(Like.created_at.desc()).all()
        
        return render_template('admin_database.html', 
                             users=users, 
                             comments=comments, 
                             likes=likes)
    except Exception as e:
        # Return detailed error info for debugging
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Admin Database Error</title></head>
        <body>
        <h1>Error in Admin Database Route</h1>
        <p><strong>Error:</strong> {e}</p>
        <pre>{error_details}</pre>
        </body>
        </html>
        """, 500

@app.route('/admin/comments')
@admin_required
def admin_comments():
    """Admin page to manage all comments"""
    try:
        from models import Comment, Project
        
        # Get all comments with related project and user info
        comments = Comment.query.order_by(Comment.created_at.desc()).all()
        
        # Group comments by project for better organization
        comments_by_project = {}
        for comment in comments:
            project_id = comment.project_id
            if project_id not in comments_by_project:
                comments_by_project[project_id] = {
                    'project': Project.query.get(project_id),
                    'comments': []
                }
            comments_by_project[project_id]['comments'].append(comment)
        
        return render_template('admin_comments.html', 
                             comments_by_project=comments_by_project,
                             total_comments=len(comments))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <html>
        <head><title>Admin Comments Error</title></head>
        <body>
        <h1>Error in Admin Comments Route</h1>
        <p><strong>Error:</strong> {e}</p>
        <pre>{error_details}</pre>
        </body>
        </html>
        """, 500

@app.route('/admin/delete_comment/<int:comment_id>', methods=['POST'])
@admin_required
def admin_delete_comment(comment_id):
    """Admin route to delete any comment"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        project_id = comment.project_id
        
        # Delete all nested replies first
        def delete_replies(comment):
            for reply in comment.replies:
                delete_replies(reply)
                db.session.delete(reply)
        
        delete_replies(comment)
        db.session.delete(comment)
        db.session.commit()
        
        flash(f'კომენტარი წარმატებით წაიშალა!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('კომენტარის წაშლისას დაფიქსირდა შეცდომა.', 'error')
        print(f"Error deleting comment: {e}")
    
    return redirect(url_for('admin_comments'))

@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
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
@admin_required
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

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    # Also ensure projects directory exists
    os.makedirs(PROJECTS_DIR, exist_ok=True)

if __name__ == '__main__':
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    # For production (Render.com), use environment variables
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
