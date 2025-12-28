import os
import time
import uuid
import io
from datetime import datetime, UTC
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail, Message
import boto3
from botocore.client import Config
import cloudinary
import cloudinary.uploader
import cloudinary.api
import json
import re
from functools import wraps
from dotenv import load_dotenv
from docx import Document
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

# Initialize Cloudflare R2 client for large files
r2_client = None
try:
    r2_access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
    r2_secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
    r2_account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
    r2_bucket = os.environ.get('CLOUDFLARE_R2_BUCKET_NAME', 'portfolio-files')

    if r2_access_key and r2_secret_key and r2_account_id and \
       not r2_access_key.startswith('your_') and not r2_secret_key.startswith('your_') and not r2_account_id.startswith('your_'):
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            config=Config(signature_version='s3v4')
        )
        print("Cloudflare R2 client initialized successfully")
    else:
        print("Cloudflare R2 credentials not configured (using placeholder values), will use local storage for large files")
except Exception as e:
    print(f"Failed to initialize Cloudflare R2 client: {e}")
    print("Will fall back to Cloudinary for file uploads")
    r2_client = None

def clean_description(text):
    """Clean description text by removing excessive line breaks and formatting"""
    if not text:
        return text
    
    # Replace multiple consecutive line breaks with maximum of 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text

def process_zip_for_3d_viewer(file, project_id):
    """Process ZIP file for 3D viewer and return HTML URL"""
    import zipfile
    import io

    file.seek(0)
    zip_data = io.BytesIO(file.read())
    uploaded_files = {}

    try:
        with zipfile.ZipFile(zip_data, 'r') as zip_file:
            # Upload all files individually to R2
            for file_info in zip_file.filelist:
                if not file_info.is_dir() and not file_info.filename.startswith('__MACOSX/'):
                    file_name = file_info.filename
                    with zip_file.open(file_name) as f:
                        file_content = f.read()

                    file_size_mb = len(file_content) / (1024 * 1024)
                    print(f"Uploading {file_name} ({file_size_mb:.1f}MB)...")

                    try:
                        if r2_client:  # Upload all files to R2
                            # Preserve folder structure in R2 key
                            r2_key = f"projects/{project_id}/3d_viewer/{file_name}"
                            r2_client.put_object(
                                Bucket=r2_bucket,
                                Key=r2_key,
                                Body=file_content,
                                ContentType='application/octet-stream'
                            )
                            file_url = f"https://pub-{r2_account_id}.r2.dev/{r2_key}"
                            uploaded_files[file_name] = file_url
                            print(f"Uploaded {file_name} to R2: {file_url}")
                        else:
                            print("R2 client not available, falling back to Cloudinary")
                            # Fallback to Cloudinary
                            import cloudinary.uploader
                            upload_result = cloudinary.uploader.upload(
                                io.BytesIO(file_content),
                                folder=f"portfolio/projects/{project_id}/3d_viewer",
                                resource_type='raw',
                                public_id=file_name.replace('/', '_').replace('\\', '_'),
                                timeout=600
                            )
                            uploaded_files[file_name] = upload_result['secure_url']
                            print(f"Uploaded {file_name} to Cloudinary: {upload_result['secure_url']}")
                    except Exception as upload_error:
                        print(f"Failed to upload {file_name}: {upload_error}")
                        # Try Cloudinary as fallback
                        try:
                            import cloudinary.uploader
                            upload_result = cloudinary.uploader.upload(
                                io.BytesIO(file_content),
                                folder=f"portfolio/projects/{project_id}/3d_viewer",
                                resource_type='raw',
                                public_id=file_name.replace('/', '_').replace('\\', '_'),
                                timeout=600
                            )
                            uploaded_files[file_name] = upload_result['secure_url']
                            print(f"Fallback upload to Cloudinary successful: {upload_result['secure_url']}")
                        except Exception as fallback_error:
                            print(f"Fallback upload also failed: {fallback_error}")
                            continue

            # Find HTML file and return its URL
            html_files = [name for name in uploaded_files.keys() if name.lower().endswith('.html')]
            if html_files:
                html_url = uploaded_files[html_files[0]]
                print(f"Found HTML file: {html_files[0]} -> {html_url}")
                return html_url
            else:
                print("No HTML file found in ZIP")
                return None

    except Exception as process_error:
        print(f"Failed to process ZIP file: {process_error}")
        return None

def extract_text_from_file(file, project_id=None):
    """Extract text content from various file types"""
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.txt'):
            # Plain text file
            content = file.read().decode('utf-8')
            return content
            
        elif filename.endswith('.md'):
            # Markdown file
            content = file.read().decode('utf-8')
            return content
            
        elif filename.endswith('.html'):
            # HTML file - extract text content
            content = file.read().decode('utf-8')
            # Simple HTML text extraction (remove tags)
            import re
            content = re.sub(r'<[^>]+>', '', content)
            return content
            
        elif filename.endswith(('.docx', '.doc')):
            # Word document
            # Reset file pointer
            file.seek(0)
            doc = Document(file)
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            return '\n\n'.join(content)
            
        elif filename.endswith('.zip'):
            # ZIP file - extract all files and upload individually to Cloudflare R2 or Cloudinary
            import zipfile
            
            file.seek(0)
            zip_data = io.BytesIO(file.read())
            uploaded_files = {}
            
            try:
                with zipfile.ZipFile(zip_data, 'r') as zip_file:
                    # Upload all files individually
                    for file_info in zip_file.filelist:
                        if not file_info.is_dir() and not file_info.filename.startswith('__MACOSX/'):
                            file_name = file_info.filename
                            with zip_file.open(file_name) as f:
                                file_content = f.read()
                            
                            file_size_mb = len(file_content) / (1024 * 1024)
                            print(f"Uploading {file_name} ({file_size_mb:.1f}MB)...")
                            
                            # Determine resource type
                            if file_name.lower().endswith(('.html', '.css', '.js', '.json')):
                                resource_type = 'raw'
                            else:
                                resource_type = 'auto'
                            
                            try:
                                if r2_client:  # Upload all files to R2 for consistency
                                    r2_key = f"projects/{project_id}/3d_viewer/{file_name}"
                                    r2_client.put_object(
                                        Bucket=r2_bucket,
                                        Key=r2_key,
                                        Body=file_content,
                                        ContentType='application/octet-stream'
                                    )
                                    file_url = f"https://pub-{r2_account_id}.r2.dev/{r2_key}"
                                    uploaded_files[file_name] = file_url
                                    print(f"Uploaded {file_name} to R2: {file_url}")
                                else:
                                    # Fallback to Cloudinary if no R2
                                    # Determine resource type
                                    if file_name.lower().endswith(('.html', '.css', '.js', '.json')):
                                        resource_type = 'raw'
                                    else:
                                        resource_type = 'auto'
                                    
                                    upload_result = cloudinary.uploader.upload(
                                        io.BytesIO(file_content),
                                        folder=f"portfolio/projects/{project_id}/3d_viewer",
                                        resource_type=resource_type,
                                        public_id=file_name.replace('/', '_').replace('\\', '_'),
                                        timeout=600
                                    )
                                    uploaded_files[file_name] = upload_result['secure_url']
                                    print(f"Uploaded {file_name} to Cloudinary: {upload_result['secure_url']}")
                            except Exception as upload_error:
                                print(f"Failed to upload {file_name}: {upload_error}")
                                continue
                    
                    # Find HTML file and return its URL
                    html_files = [name for name in uploaded_files.keys() if name.lower().endswith('.html')]
                    if html_files:
                        html_url = uploaded_files[html_files[0]]
                        print(f"Found HTML file: {html_files[0]} -> {html_url}")
                        flash(f'3D viewer HTML ფაილი მზადაა: {html_files[0]}', 'success')
                        return html_url
                    else:
                        print("No HTML file found in ZIP")
                        flash('ZIP ფაილში HTML ფაილი არ მოიძებნა', 'error')
                        return None
                        
            except Exception as process_error:
                print(f"Failed to process ZIP file: {process_error}")
                flash(f'ZIP ფაილის დამუშავება ვერ მოხერხდა: {process_error}', 'error')
                return None
            
        elif filename.endswith('.pdf'):
            # PDF file - would need PyPDF2, but for now just upload URL
            return None  # Will use URL instead
            
        else:
            # Unknown file type - return None to use URL
            return None
            
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return None

app = Flask(__name__)

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_ANON_KEY')
supabase: Client = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    print("Supabase credentials not configured, user monitoring will be disabled")

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
elif os.environ.get('FLASK_ENV') == 'development':
    db_path = os.path.join(os.getcwd(), 'instance', 'portfolio_dev.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    db_path = os.path.join(os.getcwd(), 'instance', 'portfolio.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Session configuration for better security
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour instead of 24 hours
app.config['SESSION_COOKIE_DOMAIN'] = None  # Only this domain
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Remove SERVER_NAME for now as it can cause session issues
# Only set SERVER_NAME for local development
# if os.environ.get('FLASK_ENV') != 'production':
#     app.config['SERVER_NAME'] = 'localhost:5002'
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

# Add CORS headers for API endpoints
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

PROJECTS_DIR = 'projects'
PROJECTS_JSON = 'projects.json'
COMMENTS_JSON = 'comments.json'
# Security Note: Credentials are now loaded from environment variables
# Make sure to set ADMIN_USERNAME, ADMIN_PASSWORD, ANALYTICS_USERNAME, ANALYTICS_PASSWORD in .env file
# NEVER commit the .env file to version control!

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'ogg', 'mov', 'avi', 'docx', 'html', 'pdf', 'txt', 'doc'}
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'kepulia')  # შეცვალე production-ში
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'kepulia123')  # შეცვალე production-ში

# Analytics credentials (separate from admin)
ANALYTICS_USERNAME = os.environ.get('ANALYTICS_USERNAME', 'kanalytics')
ANALYTICS_PASSWORD = os.environ.get('ANALYTICS_PASSWORD', 'kanalytics2026')

# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("✅ Database initialized successfully")
        
        # Seed database with initial projects if empty
        # DISABLED: Data has been migrated via migration scripts
        # try:
        #     # Check if any projects exist by trying to get the first one
        #     existing_project = Project.query.first()
        #     if existing_project is None:
        #         print("No projects found, seeding database...")
        #         with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
        #             projects_data = json.load(f)
        #         for proj_data in projects_data:
        #             description = ""
        #             if proj_data.get('description_file'):
        #                 desc_path = os.path.join(PROJECTS_DIR, proj_data['folder'], proj_data['description_file'])
        #                 if os.path.exists(desc_path):
        #                     with open(desc_path, 'r', encoding='utf-8') as df:
        #                         description = df.read()
        #             project = Project(
        #                 id=proj_data['id'],
        #                 title=proj_data['title'],
        #                 main_image=proj_data.get('main_image'),
        #                 other_images=json.dumps(proj_data.get('other_images', [])),
        #                 viewer3D=proj_data.get('viewer3D'),
        #                 description=description,
        #                 description_file=proj_data.get('description_file'),
        #                 folder=proj_data.get('folder'),
        #                 latitude=proj_data.get('latitude'),
        #                 longitude=proj_data.get('longitude'),
        #                 documents=json.dumps(proj_data.get('documents', [])),
        #                 loading_video=proj_data.get('loading_video'),
        #                 loading_audio=proj_data.get('loading_audio'),
        #                 project_info=json.dumps(proj_data.get('project_info', {})),
        #                 type_categories=json.dumps(proj_data.get('type_categories', [])),
        #                 period_categories=json.dumps(proj_data.get('period_categories', [])),
        #                 sort_order=0  # Default sort order
        #             )
        #             db.session.add(project)
        #         db.session.commit()
        #         print("✅ Seeded database with initial projects")
        #     else:
        #         print("Projects already exist in database, skipping seeding")
        # except Exception as e:
        #     print(f"⚠️ Could not seed database: {e}")
        #     # Don't crash the app
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

# User Monitoring Functions

def get_client_ip():
    """Get the client's real IP address"""
    if request.headers.get('X-Forwarded-For'):
        # Handle comma-separated IPs (first one is the original client)
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    return ip

def track_user_visit(page_url=None, user_agent=None, screen_resolution=None, referrer=None):
    """Track user visit and store in Supabase"""
    if not supabase:
        return False
    
    try:
        # Get user data
        ip_address = get_client_ip()
        
        # Validate IP address - if invalid, set to None
        if not ip_address or ip_address == 'None':
            ip_address = None
        
        # Get session ID safely
        session_id = None
        try:
            session_id = session.get('user_session_id')
        except RuntimeError:
            # Outside request context
            session_id = str(uuid.uuid4())
        
        # Generate session ID if not exists
        if not session_id:
            session_id = str(uuid.uuid4())
            try:
                session['user_session_id'] = session_id
            except RuntimeError:
                # Outside request context, can't set session
                pass
        
        # Get user ID safely
        user_id = None
        try:
            if current_user.is_authenticated:
                user_id = current_user.id
        except RuntimeError:
            # Outside request context
            pass
        
        # Prepare data for Supabase
        visit_data = {
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': user_agent or (request.headers.get('User-Agent') if request else 'Unknown'),
            'page_url': page_url or (request.url if request else 'Unknown'),
            'screen_resolution': screen_resolution,
            'referrer': referrer or (request.referrer if request else None),
            'timestamp': datetime.now(UTC).isoformat(),
            'user_id': user_id,
            'action': 'page_view'  # Always set action
        }
        
        # Insert into Supabase
        result = supabase.table('user_visits').insert(visit_data).execute()
        return True
        
    except Exception as e:
        print(f"Failed to track user visit: {e}")
        return False

def get_user_analytics(days=30):
    """Get user analytics from Supabase"""
    print(f"Getting user analytics for {days} days")
    print(f"Supabase client available: {supabase is not None}")
    
    if not supabase:
        print("No Supabase client, returning None")
        return None
    
    try:
        # Calculate the timestamp for N days ago
        from datetime import timedelta
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        print(f"Cutoff date: {cutoff_iso}")
        
        # Get visits from last N days
        result = supabase.table('user_visits').select('*').gte('timestamp', cutoff_iso).execute()
        print(f"Retrieved {len(result.data) if result.data else 0} records")
        return result.data
    except Exception as e:
        print(f"Failed to get user analytics: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_projects():
    """Load projects from database primarily, JSON as fallback"""
    try:
        # Load from database first (now that we're using PostgreSQL)
        # Sort by sort_order (ascending - lower numbers first), then by created_at (newest first)
        projects = Project.query.order_by(Project.sort_order.asc(), Project.created_at.desc()).all()
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
                'model_urls': json.loads(project.model_urls) if project.model_urls else [],
                'viewer3D': project.viewer3D,
                'description': description,
                'description_file': project.description_file,
                'folder': project.folder,
                'latitude': project.latitude,
                'longitude': project.longitude,
                'sort_order': project.sort_order,
                'documents': json.loads(project.documents) if project.documents else [],
                'loading_video': project.loading_video,
                'loading_audio': project.loading_audio,
                'project_info': json.loads(project.project_info) if project.project_info else {},
                'type_categories': json.loads(project.type_categories) if project.type_categories else [],
                'period_categories': json.loads(project.period_categories) if project.period_categories else []
            })
        print(f"✅ Loaded {len(result)} projects from database")
        return result
    except Exception as e:
        print(f"❌ Error loading projects from database: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to JSON if database fails
    try:
        if os.path.exists(PROJECTS_JSON):
            with open(PROJECTS_JSON, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
            print(f"✅ Loaded {len(projects_data)} projects from JSON (fallback)")
            return projects_data
    except Exception as e:
        print(f"❌ Error loading projects from JSON: {e}")
    
    return []

def save_projects(projects):
    """Save projects to JSON primarily, database as backup"""
    print(f"DEBUG: save_projects called with {len(projects)} projects")
    try:
        # Save to JSON first
        with open(PROJECTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved {len(projects)} projects to JSON")
        
        # Also save to database for compatibility
        try:
            # Get existing project IDs
            existing_ids = {p.id for p in Project.query.all()}

            # Track which projects we're updating/adding
            updated_ids = set()

            for project_data in projects:
                project_id = project_data['id']
                updated_ids.add(project_id)

                # Check if project exists
                existing_project = Project.query.get(project_id)
                if existing_project:
                    # Update existing project
                    existing_project.title = project_data['title']
                    existing_project.main_image = project_data.get('main_image')
                    existing_project.main_image_caption = project_data.get('main_image_caption')
                    existing_project.other_images = json.dumps(project_data.get('other_images', []))
                    existing_project.viewer3D = project_data.get('viewer3D')
                    existing_project.description = project_data.get('description')
                    existing_project.description_file = project_data.get('description_file')
                    existing_project.folder = project_data.get('folder')
                    existing_project.latitude = project_data.get('latitude')
                    existing_project.longitude = project_data.get('longitude')
                    existing_project.sort_order = project_data.get('sort_order', 0)
                    existing_project.documents = json.dumps(project_data.get('documents', []))
                    existing_project.loading_video = project_data.get('loading_video')
                    existing_project.loading_audio = project_data.get('loading_audio')
                    existing_project.project_info = json.dumps(project_data.get('project_info', {}))
                    existing_project.type_categories = json.dumps(project_data.get('type_categories', []))
                    existing_project.period_categories = json.dumps(project_data.get('period_categories', []))
                else:
                    # Create new project
                    project = Project(
                        id=project_id,
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
                        sort_order=project_data.get('sort_order', 0),
                        documents=json.dumps(project_data.get('documents', [])),
                        loading_video=project_data.get('loading_video'),
                        loading_audio=project_data.get('loading_audio'),
                        project_info=json.dumps(project_data.get('project_info', {})),
                        type_categories=json.dumps(project_data.get('type_categories', [])),
                        period_categories=json.dumps(project_data.get('period_categories', []))
                    )
                    db.session.add(project)

            # Remove projects that are no longer in the list
            for old_id in existing_ids - updated_ids:
                Project.query.filter_by(id=old_id).delete()

            db.session.commit()
            print(f"✅ Also saved {len(projects)} projects to database")
        except Exception as db_error:
            print(f"⚠️ Database save failed: {db_error}")
            
    except Exception as e:
        print(f"❌ Error saving projects to JSON: {e}")
        import traceback
        traceback.print_exc()

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

def analytics_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('analytics_logged_in'):
            return redirect(url_for('analytics_login', next=request.url))
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
        'model_urls': json.loads(project_db.model_urls) if project_db.model_urls else [],
        'viewer3D': project_db.viewer3D,
        'description': project_db.description,
        'description_file': project_db.description_file,
        'folder': project_db.folder,
        'latitude': project_db.latitude,
        'longitude': project_db.longitude,
        'sort_order': project_db.sort_order,
        'documents': json.loads(project_db.documents) if project_db.documents else [],
        'loading_video': project_db.loading_video,
        'loading_audio': project_db.loading_audio,
        'project_info': json.loads(project_db.project_info) if project_db.project_info else {},
        'type_categories': json.loads(project_db.type_categories) if project_db.type_categories else [],
        'period_categories': json.loads(project_db.period_categories) if project_db.period_categories else []
    }
    
    if request.method == 'POST':
        try:
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
            sort_order = request.form.get('sort_order', '0').strip()
            if latitude:
                project_db.latitude = latitude
            if longitude:
                project_db.longitude = longitude
            try:
                project_db.sort_order = int(sort_order) if sort_order else 0
            except ValueError:
                project_db.sort_order = 0
                
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
            
            # Handle file uploads to Cloudinary
            uploaded_urls = []
            
            # Upload image files
            image_files = request.files.getlist('image_files')
            for file in image_files:
                if file and file.filename:
                    try:
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}")
                        uploaded_urls.append({
                            'url': upload_result['secure_url'],
                            'caption': f"ატვირთული სურათი: {file.filename}",
                            'type': 'image'
                        })
                        print(f"Uploaded image {file.filename} to Cloudinary: {upload_result['secure_url']}")
                        flash(f'სურათი წარმატებით აიტვირთა: {file.filename}', 'success')
                    except Exception as e:
                        print(f"Failed to upload image {file.filename}: {e}")
                        flash(f'სურათის ატვირთვა ვერ მოხერხდა: {file.filename}', 'error')
                    flash(f'სურათის ატვირთვა ვერ მოხერხდა: {file.filename}', 'error')
        
                    # Upload 3D model files
                    model_files = request.files.getlist('model_files')
                    for file in model_files:
                        if file and file.filename:
                            filename_lower = file.filename.lower()
                            try:
                                if filename_lower.endswith('.zip'):
                                    # For ZIP files, extract HTML content for 3D viewer
                                    extracted_html = extract_text_from_file(file, project_id)
                                    if extracted_html:
                                        # Save HTML content to viewer3D field
                                        project_db.viewer3D = extracted_html
                                        print(f"Extracted HTML from 3D ZIP file {file.filename} and saved to viewer3D field")
                                        flash(f'3D ZIP ფაილიდან HTML ექსტრაქცია შესრულებულია: {file.filename}', 'success')
                                    else:
                                        # If no HTML found, upload ZIP to Cloudinary
                                        upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}/models", resource_type="raw")
                                        uploaded_urls.append({
                                            'url': upload_result['secure_url'],
                                            'caption': f"3D ZIP ფაილი: {file.filename}",
                                            'type': 'model'
                                        })
                                        print(f"Uploaded 3D ZIP file {file.filename} to Cloudinary: {upload_result['secure_url']}")
                                        flash(f'3D ZIP ფაილი აიტვირთა: {file.filename}', 'success')
                                else:
                                    # For regular 3D files, upload to Cloudinary
                                    upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}/models", resource_type="auto")
                                    uploaded_urls.append({
                                        'url': upload_result['secure_url'],
                                        'caption': f"3D მოდელი: {file.filename}",
                                        'type': 'model'
                                    })
                                    print(f"Uploaded 3D model {file.filename} to Cloudinary: {upload_result['secure_url']}")
                                    flash(f'3D მოდელი აიტვირთა: {file.filename}', 'success')
                            except Exception as e:
                                print(f"Failed to upload 3D file {file.filename}: {e}")
                                flash(f'3D ფაილის ატვირთვა ვერ მოხერხდა: {file.filename}', 'error')
        
                    # Upload description file
                    description_file = request.files.get('description_file')
                    if description_file and description_file.filename:
                        try:
                            # Try to extract text from the file
                            extracted_text = extract_text_from_file(description_file, project_id)
                            
                            if extracted_text:
                                filename_lower = description_file.filename.lower()
                                if filename_lower.endswith('.zip'):
                                    # For ZIP files (3D viewers), save HTML content to viewer3D field
                                    project_db.viewer3D = extracted_text
                                    project_db.description_file = None
                                    print(f"Extracted HTML from 3D ZIP file {description_file.filename} and saved to viewer3D field")
                                    flash(f'3D ZIP ფაილიდან HTML ექსტრაქცია შესრულებულია: {description_file.filename}', 'success')
                                else:
                                    # For other text files, save to description field
                                    project_db.description = clean_description(extracted_text)
                                    project_db.description_file = None  # Clear file URL since we have text
                                    print(f"Extracted text from description file {description_file.filename} and saved to description field")
                                    flash(f'აღწერის ტექსტი ექსტრაქტირებულია: {description_file.filename}', 'success')
                            else:
                                # If text extraction failed, upload file to Cloudinary and save URL
                                upload_result = cloudinary.uploader.upload(description_file, folder=f"portfolio/projects/{project_id}/docs", resource_type="raw")
                                project_db.description_file = upload_result['secure_url']
                                print(f"Uploaded description file {description_file.filename} to Cloudinary: {upload_result['secure_url']}")
                        except Exception as e:
                            print(f"Failed to process description file {description_file.filename}: {e}")
                            flash(f'აღწერის ფაილის დამუშავება ვერ მოხერხდა: {description_file.filename}', 'error')
            
            # Add uploaded URLs to existing images
            if uploaded_urls:
                # Get existing other_images
                existing_other_images = other_images.copy()
                existing_model_urls = json.loads(project_db.model_urls) if project_db.model_urls else []
                
                # Add uploaded files to appropriate arrays
                for uploaded in uploaded_urls:
                    if uploaded['type'] == 'image':
                        existing_other_images.append({
                            'url': uploaded['url'],
                            'caption': uploaded['caption']
                        })
                    elif uploaded['type'] == 'model':
                        existing_model_urls.append({
                            'url': uploaded['url'],
                            'caption': uploaded['caption']
                        })
                
                # Update database
                project_db.other_images = json.dumps(existing_other_images) if existing_other_images else None
                project_db.model_urls = json.dumps(existing_model_urls) if existing_model_urls else None
                
                flash(f'ატვირთულია {len(uploaded_urls)} ფაილი Cloudinary-ზე!', 'success')
            
            # Commit changes (moved outside the uploaded_urls condition)
            try:
                db.session.commit()
                flash('პროექტი წარმატებით განახლდა!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('შეცდომა პროექტის განახლებისას.', 'error')
                return redirect(url_for('edit_project', project_id=project_id))
                    
            return redirect(url_for('admin_panel'))
        except Exception as e:
            print(f"Unexpected error in edit_project POST processing: {e}")
            flash('შეცდომა ფორმის დამუშავებისას.', 'error')
            return redirect(url_for('edit_project', project_id=project_id))
    
    return render_template('edit_project.html', project=project, description=project['description'])

# User Monitoring API Endpoints

@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    """API endpoint to track user visits"""
    try:
        data = request.get_json() or {}
        print(f"Track visit called with data: {data}")
        print(f"Supabase client available: {supabase is not None}")
        
        # Track the visit
        success = track_user_visit(
            page_url=data.get('page_url'),
            user_agent=data.get('user_agent'),
            screen_resolution=data.get('screen_resolution'),
            referrer=data.get('referrer')
        )
        
        print(f"Tracking result: {success}")
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to track visit'}), 500
            
    except Exception as e:
        print(f"Error in track_visit: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/debug-supabase')
def debug_supabase():
    """Debug endpoint to check Supabase configuration"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')
    
    return jsonify({
        'supabase_url_configured': bool(supabase_url),
        'supabase_key_configured': bool(supabase_key),
        'supabase_client_initialized': supabase is not None,
        'supabase_url_masked': supabase_url[:20] + '...' if supabase_url else None,
        'supabase_key_masked': supabase_key[:10] + '...' if supabase_key else None
    })

@app.route('/api/test-tracking')
def test_tracking():
    """Test endpoint to manually create a tracking record"""
    success = track_user_visit(
        page_url='https://test-domain.com/test-page',
        user_agent='Test User Agent',
        screen_resolution='1920x1080',
        referrer='https://test-domain.com/'
    )
    
    return jsonify({
        'tracking_success': success,
        'supabase_available': supabase is not None,
        'message': 'Test tracking completed' if success else 'Test tracking failed'
    })

@app.route('/analytics/login', methods=['GET', 'POST'])
def analytics_login():
    # Temporarily disabled rate limiting for debugging
    # Rate limiting: max 5 attempts per 15 minutes
    # now = datetime.utcnow().timestamp()
    # attempts = session.get('analytics_login_attempts', [])
    # Clean old attempts (older than 15 minutes)
    # attempts = [t for t in attempts if now - t < 900]
    
    # if len(attempts) >= 5:
    #     flash('ხშირი შესვლის მცდელობა. გთხოვთ სცადოთ 15 წუთში.', 'error')
    #     return render_template('analytics_login.html')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ANALYTICS_USERNAME and password == ANALYTICS_PASSWORD:
            session['analytics_logged_in'] = True
            # session.pop('analytics_login_attempts', None)  # Reset attempts on success
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('analytics_dashboard'))
        else:
            # Record failed attempt
            # attempts.append(now)
            # session['analytics_login_attempts'] = attempts
            flash('არასწორი მონაცემები')
    return render_template('analytics_login.html')

@app.route('/analytics')
@analytics_required
def analytics_dashboard():
    """Analytics dashboard - requires analytics login"""
    
    # Get analytics data
    analytics_data = get_user_analytics(days=30)
    
    # Process data for display
    stats = {
        'total_visits': 0,
        'unique_sessions': 0,
        'unique_ips': 0,
        'authenticated_users': 0,
        'screen_resolutions': [],
        'popular_pages': [],
        'recent_visits': []
    }
    
    if analytics_data:
        # Calculate statistics
        sessions = set()
        ips = set()
        auth_users = set()
        pages = {}
        resolutions = set()
        
        for visit in analytics_data:
            stats['total_visits'] += 1
            sessions.add(visit['session_id'])
            if visit['ip_address']:
                ips.add(visit['ip_address'])
            if visit['user_id']:
                auth_users.add(visit['user_id'])
            if visit['page_url']:
                pages[visit['page_url']] = pages.get(visit['page_url'], 0) + 1
            if visit['screen_resolution']:
                resolutions.add(visit['screen_resolution'])
        
        stats['unique_sessions'] = len(sessions)
        stats['unique_ips'] = len(ips)
        stats['authenticated_users'] = len(auth_users)
        stats['screen_resolutions'] = list(resolutions)
        stats['popular_pages'] = sorted(pages.items(), key=lambda x: x[1], reverse=True)[:10]
        stats['recent_visits'] = analytics_data[-20:]  # Last 20 visits
        
        # Calculate unique IPs in recent visits
        recent_ips = set()
        for visit in stats['recent_visits']:
            if visit['ip_address']:
                recent_ips.add(visit['ip_address'])
        stats['unique_ips_recent'] = len(recent_ips)
        
        # Calculate detailed IP statistics
        stats['unique_ips_list'] = []
        for ip in sorted(ips):
            ip_visits = [v for v in analytics_data if v['ip_address'] == ip]
            user_agents = list(set(v['user_agent'] for v in ip_visits if v['user_agent']))
            screen_resolutions = list(set(v['screen_resolution'] for v in ip_visits if v['screen_resolution']))
            pages_visited = list(set(v['page_url'] for v in ip_visits if v['page_url']))
            
            stats['unique_ips_list'].append({
                'ip': ip,
                'visit_count': len(ip_visits),
                'first_visit': min(v['timestamp'] for v in ip_visits),
                'last_visit': max(v['timestamp'] for v in ip_visits),
                'user_agents': user_agents,
                'screen_resolutions': screen_resolutions,
                'pages_visited': pages_visited,
                'visits': sorted(ip_visits, key=lambda x: x['timestamp'], reverse=True)[:10]  # Last 10 visits for this IP
            })
    
    return render_template('admin_analytics.html', stats=stats, analytics_data=analytics_data)

@app.route('/analytics/logout')
def analytics_logout():
    """Logout from analytics dashboard"""
    session.pop('analytics_logged_in', None)
    return redirect(url_for('analytics_login'))

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

@app.route('/contact')
def contact():
    """Contact/CV page"""
    return render_template('contact.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

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
    # Temporarily disabled rate limiting for debugging
    # Rate limiting: max 5 attempts per 15 minutes
    # now = datetime.utcnow().timestamp()
    # attempts = session.get('login_attempts', [])
    # Clean old attempts (older than 15 minutes)
    # attempts = [t for t in attempts if now - t < 900]
    
    # if len(attempts) >= 5:
    #     flash('ხშირი შესვლის მცდელობა. გთხოვთ სცადოთ 15 წუთში.', 'error')
    #     return render_template('login.html')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            # session.pop('login_attempts', None)  # Reset attempts on success
            return redirect(url_for('admin_panel'))
        else:
            # Record failed attempt
            # attempts.append(now)
            # session['login_attempts'] = attempts
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/debug/session')
def debug_session():
    """Debug route to check session status"""
    return f"""
    <html>
    <head><title>Session Debug</title></head>
    <body>
    <h1>Session Debug Info</h1>
    <p><strong>Session data:</strong> {dict(session)}</p>
    <p><strong>logged_in value:</strong> {session.get('logged_in')}</p>
    <p><strong>analytics_logged_in value:</strong> {session.get('analytics_logged_in')}</p>
    <p><strong>login_attempts:</strong> {session.get('login_attempts', [])}</p>
    <p><strong>analytics_login_attempts:</strong> {session.get('analytics_login_attempts', [])}</p>
    <p><strong>Current user:</strong> {current_user.is_authenticated if current_user else 'None'}</p>
    <p><strong>Request remote addr:</strong> {request.remote_addr}</p>
    <p><strong>Request host:</strong> {request.host}</p>
    <br>
    <a href="/admin">Go to Admin Login</a> | <a href="/analytics/login">Go to Analytics Login</a>
    </body>
    </html>
    """

@app.route('/admin/panel')
@admin_required
def admin_panel():
    projects = load_projects()
    return render_template('admin_panel.html', projects=projects)

@app.route('/admin/logout')
def admin_logout():
    """Logout from admin panel"""
    print(f"DEBUG: Before logout - session: {dict(session)}")
    session.clear()
    # Clear session cookie
    response = redirect(url_for('admin_login'))
    response.set_cookie('session', '', expires=0)
    print(f"DEBUG: After logout - session: {dict(session)}")
    flash('თქვენ გახვედით ადმინ პანელიდან.', 'info')
    return response

@app.route('/export-comments')
def export_comments_public():
    """Export all comments as JSON - public route for syncing"""
    try:
        comments = load_comments()
        return jsonify(comments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export-projects')
def export_projects_public():
    """Export all projects as JSON - public route for syncing"""
    try:
        projects = load_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/export-projects')
def export_projects():
    """Export all projects as JSON - temporary route for syncing"""
    try:
        projects = load_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    print("DEBUG: Upload route called - Method:", request.method)
    print("DEBUG: Content-Type:", request.content_type)
    print("DEBUG: Content-Length:", request.content_length)
    
    # Log to file for debugging
    with open('upload_debug.log', 'a', encoding='utf-8') as f:
        f.write(f"Upload called - Method: {request.method}, Content-Type: {request.content_type}\n")
    
    if request.method == 'POST':
        print("DEBUG: POST request received")
        with open('upload_debug.log', 'a', encoding='utf-8') as f:
            f.write("POST request received\n")
        try:
            title = request.form['title']
            description = request.form['description']
            viewer3d = request.form['viewer3d']
            print(f"DEBUG: Form data received - title: {title}")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Form data - title: {title}\n")
                
            # Continue with processing
            print("DEBUG: Starting image processing")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write("Starting image processing\n")
                
        except KeyError as e:
            print(f"DEBUG: Missing form field: {e}")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Missing form field: {e}\n")
            flash('ფორმის მონაცემები არასწორია.', 'error')
            return redirect(url_for('upload_project'))
        except Exception as e:
            print(f"DEBUG: Unexpected error in form processing: {e}")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Unexpected error in form processing: {e}\n")
            flash('შეცდომა ფორმის დამუშავებისას.', 'error')
            return redirect(url_for('upload_project'))
        loading_video = request.form.get('loading_video', '')
        loading_audio = request.form.get('loading_audio', '')
        
        # Handle all images from the unified system
        all_images = []
        main_image_url = None
        main_image_caption = ""
        selected_main = request.form.get('main_image_selector', '0')  # Default to first image
        
        print("DEBUG: Processing images")
        with open('upload_debug.log', 'a', encoding='utf-8') as f:
            f.write("Processing images\n")
            
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
                    main_image_caption = image_caption
            elif i == 0:
                pass  # Check at least the first one
            else:
                break
            i += 1
        
        print(f"DEBUG: Found {len(all_images)} images")
        with open('upload_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"Found {len(all_images)} images\n")
        
        # If no main image selected, use first image
        if not main_image_url and all_images:
            main_image_url = all_images[0]['url']
            main_image_caption = all_images[0]['caption']
        
        # Create other_images array (exclude the main image)
        other_images = []
        for img in all_images:
            if img['url'] != main_image_url:
                other_images.append({
                    'url': img['url'],
                    'caption': img['caption']
                })
        
        project_id = secure_filename(title.lower().replace(' ', '_'))
        print(f"DEBUG: Generated project_id: '{project_id}' from title: '{title}'")
        if not project_id:
            # Use timestamp-based ID for non-ASCII titles
            import time
            project_id = f"project_{int(time.time())}"
            print(f"DEBUG: Using timestamp-based project_id: '{project_id}'")
        
        project_path = os.path.join(PROJECTS_DIR, project_id)
        print(f"DEBUG: Project path: {project_path}")
        os.makedirs(project_path, exist_ok=True)
        
        # Save description
        with open(os.path.join(project_path, 'description.txt'), 'w', encoding='utf-8') as f:
            f.write(description)
        
        # Save project directly to database
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
        
        # Get sort_order
        sort_order = request.form.get('sort_order', '0').strip()
        try:
            sort_order = int(sort_order) if sort_order else 0
        except ValueError:
            sort_order = 0
        
        # Check if project already exists
        existing_project = Project.query.get(project_id)
        if existing_project:
            # Update existing project
            existing_project.title = title
            existing_project.main_image = main_image_url
            existing_project.main_image_caption = main_image_caption
            existing_project.other_images = json.dumps(other_images)
            existing_project.viewer3D = viewer3d
            existing_project.description = description
            existing_project.description_file = 'description.txt'
            existing_project.folder = project_id
            existing_project.latitude = latitude
            existing_project.longitude = longitude
            existing_project.sort_order = sort_order
            existing_project.documents = json.dumps([])
            existing_project.loading_video = loading_video
            existing_project.loading_audio = loading_audio
            existing_project.project_info = json.dumps(project_info)
            existing_project.type_categories = json.dumps(type_categories)
            existing_project.period_categories = json.dumps(period_categories)
            existing_project.model_urls = json.dumps([])  # Initialize if not set
        else:
            # Create new project
            new_project = Project(
                id=project_id,
                title=title,
                main_image=main_image_url,
                main_image_caption=main_image_caption,
                other_images=json.dumps(other_images),
                viewer3D=viewer3d,
                description=description,
                description_file='description.txt',
                folder=project_id,
                latitude=latitude,
                longitude=longitude,
                sort_order=sort_order,
                documents=json.dumps([]),
                loading_video=loading_video,
                loading_audio=loading_audio,
                project_info=json.dumps(project_info),
                type_categories=json.dumps(type_categories),
                period_categories=json.dumps(period_categories),
                model_urls=json.dumps([])
            )
            db.session.add(new_project)
        
        # Handle ZIP file uploads for 3D models
        try:
            zip_files = request.files.getlist('zip_files')
            if zip_files:
                print("DEBUG: Processing ZIP files for 3D models")
                with open('upload_debug.log', 'a', encoding='utf-8') as f:
                    f.write("Processing ZIP files for 3D models\n")
                
                for zip_file in zip_files:
                    if zip_file and zip_file.filename:
                        try:
                            print(f"DEBUG: Processing ZIP file: {zip_file.filename}")
                            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Processing ZIP file: {zip_file.filename}\n")
                            
                            # Process ZIP file and upload to R2
                            viewer3d_url = process_zip_for_3d_viewer(zip_file, project_id)
                            if viewer3d_url:
                                # Update the project's viewer3D field with the HTML URL
                                if existing_project:
                                    existing_project.viewer3D = viewer3d_url
                                else:
                                    new_project.viewer3D = viewer3d_url
                                print(f"DEBUG: Updated viewer3D URL: {viewer3d_url}")
                                with open('upload_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"Updated viewer3D URL: {viewer3d_url}\n")
                                flash(f'3D მოდელი წარმატებით აიტვირთა: {zip_file.filename}', 'success')
                            else:
                                flash(f'3D ZIP ფაილის დამუშავება ვერ მოხერხდა: {zip_file.filename}. შეამოწმეთ რომ ფაილში არის HTML ფაილი.', 'error')
                        except Exception as e:
                            print(f"DEBUG: Error processing ZIP file {zip_file.filename}: {e}")
                            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"Error processing ZIP file {zip_file.filename}: {e}\n")
                            flash(f'ZIP ფაილის დამუშავება ვერ მოხერხდა: {zip_file.filename}', 'error')
        except Exception as e:
            print(f"DEBUG: Error in ZIP processing block: {e}")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Error in ZIP processing block: {e}\n")
            flash('შეცდომა ZIP ფაილების დამუშავებისას.', 'error')
        
        # Handle file uploads to Cloudinary
        try:
            uploaded_urls = []
            
            # Upload image files
            image_files = request.files.getlist('image_files')
            for file in image_files:
                if file and file.filename:
                    try:
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}")
                        uploaded_urls.append({
                            'url': upload_result['secure_url'],
                            'caption': f"ატვირთული სურათი: {file.filename}",
                            'type': 'image'
                        })
                        print(f"Uploaded image {file.filename} to Cloudinary: {upload_result['secure_url']}")
                        flash(f'სურათი წარმატებით აიტვირთა: {file.filename}', 'success')
                    except Exception as e:
                        print(f"Failed to upload image {file.filename}: {e}")
                        flash(f'სურათის ატვირთვა ვერ მოხერხდა: {file.filename}', 'error')
            
            # Upload 3D model files
            model_files = request.files.getlist('model_files')
            for file in model_files:
                if file and file.filename:
                    filename_lower = file.filename.lower()
                    try:
                        if filename_lower.endswith('.zip'):
                            # For ZIP files, extract HTML content for 3D viewer
                            extracted_html = extract_text_from_file(file, project_id)
                            if extracted_html:
                                # Save HTML content to viewer3D field
                                if existing_project:
                                    existing_project.viewer3D = extracted_html
                                else:
                                    new_project.viewer3D = extracted_html
                                print(f"Extracted HTML from 3D ZIP file {file.filename} and saved to viewer3D field")
                                flash(f'3D ZIP ფაილიდან HTML ექსტრაქცია შესრულებულია: {file.filename}', 'success')
                            else:
                                # If no HTML found, upload ZIP to Cloudinary
                                upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}/models", resource_type="raw")
                                uploaded_urls.append({
                                    'url': upload_result['secure_url'],
                                    'caption': f"3D ZIP ფაილი: {file.filename}",
                                    'type': 'model'
                                })
                                print(f"Uploaded 3D ZIP file {file.filename} to Cloudinary: {upload_result['secure_url']}")
                                flash(f'3D ZIP ფაილი აიტვირთა: {file.filename}', 'success')
                        else:
                            # For regular 3D files, upload to Cloudinary
                            upload_result = cloudinary.uploader.upload(file, folder=f"portfolio/projects/{project_id}/models", resource_type="auto")
                            uploaded_urls.append({
                                'url': upload_result['secure_url'],
                                'caption': f"3D მოდელი: {file.filename}",
                                'type': 'model'
                            })
                            print(f"Uploaded 3D model {file.filename} to Cloudinary: {upload_result['secure_url']}")
                            flash(f'3D მოდელი აიტვირთა: {file.filename}', 'success')
                    except Exception as e:
                        print(f"Failed to upload 3D file {file.filename}: {e}")
                        flash(f'3D ფაილის ატვირთვა ვერ მოხერხდა: {file.filename}', 'error')
            
            # Upload description file
            description_file = request.files.get('description_file')
            if description_file and description_file.filename:
                try:
                    # Try to extract text from the file
                    extracted_text = extract_text_from_file(description_file, project_id)
                    
                    if extracted_text:
                        filename_lower = description_file.filename.lower()
                        if filename_lower.endswith('.zip'):
                            # For ZIP files (3D viewers), save HTML content to viewer3D field
                            if existing_project:
                                existing_project.viewer3D = extracted_text
                            else:
                                new_project.viewer3D = extracted_text
                            if existing_project:
                                existing_project.description_file = None
                            else:
                                new_project.description_file = None
                            print(f"Extracted HTML from 3D ZIP file {description_file.filename} and saved to viewer3D field")
                            flash(f'3D ZIP ფაილიდან HTML ექსტრაქცია შესრულებულია: {description_file.filename}', 'success')
                        else:
                            # For other text files, save to description field
                            if existing_project:
                                existing_project.description = clean_description(extracted_text)
                                existing_project.description_file = None  # Clear file URL since we have text
                            else:
                                new_project.description = clean_description(extracted_text)
                                new_project.description_file = None  # Clear file URL since we have text
                            print(f"Extracted text from description file {description_file.filename} and saved to description field")
                            flash(f'აღწერის ტექსტი ექსტრაქტირებულია: {description_file.filename}', 'success')
                    else:
                        # If text extraction failed, upload file to Cloudinary and save URL
                        upload_result = cloudinary.uploader.upload(description_file, folder=f"portfolio/projects/{project_id}/docs", resource_type="raw")
                        if existing_project:
                            existing_project.description_file = upload_result['secure_url']
                        else:
                            new_project.description_file = upload_result['secure_url']
                        print(f"Uploaded description file {description_file.filename} to Cloudinary: {upload_result['secure_url']}")
                except Exception as e:
                    print(f"Failed to process description file {description_file.filename}: {e}")
                    flash(f'აღწერის ფაილის დამუშავება ვერ მოხერხდა: {description_file.filename}', 'error')
            
            # Add uploaded URLs to existing images
            if uploaded_urls:
                # Get existing other_images
                existing_other_images = other_images.copy()
                existing_model_urls = json.loads(existing_project.model_urls) if existing_project and existing_project.model_urls else []
                if not existing_project:
                    existing_model_urls = []
                
                # Add uploaded files to appropriate arrays
                for uploaded in uploaded_urls:
                    if uploaded['type'] == 'image':
                        existing_other_images.append({
                            'url': uploaded['url'],
                            'caption': uploaded['caption']
                        })
                    elif uploaded['type'] == 'model':
                        existing_model_urls.append({
                            'url': uploaded['url'],
                            'caption': uploaded['caption']
                        })
                
                # Update database
                if existing_project:
                    existing_project.other_images = json.dumps(existing_other_images) if existing_other_images else None
                    existing_project.model_urls = json.dumps(existing_model_urls) if existing_model_urls else None
                else:
                    new_project.other_images = json.dumps(existing_other_images) if existing_other_images else None
                    new_project.model_urls = json.dumps(existing_model_urls) if existing_model_urls else None
                
                flash(f'ატვირთულია {len(uploaded_urls)} ფაილი Cloudinary-ზე!', 'success')
        except Exception as e:
            print(f"DEBUG: Error in file upload block: {e}")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Error in file upload block: {e}\n")
            flash('შეცდომა ფაილების ატვირთვისას.', 'error')
        
        # Commit the project to database (moved outside the file upload exception handler)
        try:
            db.session.commit()
            print("DEBUG: Project saved successfully to database")
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write("Project saved successfully to database\n")
            flash('პროექტი წარმატებით შეინახა!', 'success')
        except Exception as e:
            print(f"DEBUG: Error saving project to database: {e}")
            db.session.rollback()
            with open('upload_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Error saving project to database: {e}\n")
            flash('შეცდომა პროექტის შენახვისას.', 'error')
            return redirect(url_for('upload_project'))
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

@app.route('/projects/<project_id>/3d_viewer/<path:filename>')
def project_3d_viewer_file(project_id, filename):
    return send_from_directory(os.path.join(PROJECTS_DIR, project_id, '3d_viewer'), filename)

@app.route('/check_admin')
def check_admin():
    logged_in = session.get('logged_in', False)
    admin_ip = session.get('admin_ip')
    current_ip = request.remote_addr
    return f"""
    Logged in: {logged_in}<br>
    Admin IP: {admin_ip}<br>
    Current IP: {current_ip}<br>
    IP Match: {admin_ip == current_ip}
    """

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
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
