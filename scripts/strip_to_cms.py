"""One-time script: strip legacy app.py to CMS-only routes."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "archive" / "legacy_app.py").read_text(encoding="utf-8")

# Remove route blocks by function name (from @app.route before def X to next @app.route at col 0)
REMOVE_FUNCS = {
    "track_visit",
    "debug_supabase",
    "test_tracking",
    "ga_status",
    "analytics_login",
    "analytics_dashboard",
    "analytics_logout",
    "debug",
    "admin_users",
    "register",
    "login",
    "logout",
    "verify_email",
    "forgot_password",
    "reset_password",
    "resend_verification",
    "debug_project_detail",
    "add_comment",
    "toggle_like",
    "delete_comment",
    "debug_session",
    "export_comments_public",
    "export_projects_public",
    "debug_database",
    "debug_cloudinary",
    "admin_database",
    "admin_comments",
    "admin_delete_comment",
    "check_admin",
}

# Remove helper blocks
REMOVE_HELPERS = [
    r"# User Monitoring API Endpoints\n\n",
    r"# User Monitoring Functions\n\n",
    r"def track_user_visit\([^)]*\):.*?(?=\n(?:def |@app\.route|# Initialize database))",
    r"def get_user_analytics\([^)]*\):.*?(?=\n(?:def |@app\.route|# Initialize database))",
    r"def export_comments_data\(\):.*?(?=\n(?:def |@app\.route))",
    r"def analytics_required\(f\):.*?(?=\n(?:def |@app\.route))",
    r"def dev_only\(view\):.*?(?=\n# Initialize Cloudflare)",
    r"def sync_export_allowed\(\):.*?(?=\n(?:def |IS_PRODUCTION))",
    r"def sync_export_required\(view\):.*?(?=\n(?:def |# Initialize Cloudflare))",
]

for pat in REMOVE_HELPERS:
    src = re.sub(pat, "", src, flags=re.DOTALL)

for name in REMOVE_FUNCS:
    pat = rf"@app\.route\([^)]*\)\n(?:@\w+\n)*def {name}\([^)]*\):.*?(?=\n@app\.route|\nif __name__)"
    src = re.sub(pat, "", src, flags=re.DOTALL)

# Clean imports
replacements = [
    ("import secrets\n", ""),
    ("from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash, abort\n",
     "from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash\n"),
    ("from flask_login import LoginManager, login_user, logout_user, login_required, current_user\n", ""),
    ("from flask_mail import Mail, Message\n", ""),
    ("from supabase import create_client, Client\n", ""),
    ('from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm\n', ""),
    ("from models import db, User, Comment, Like, Project, SiteSetting, VisitEvent\n",
     "from models import db, Project, SiteSetting\n"),
]

for old, new in replacements:
    src = src.replace(old, new)

# Remove supabase block
src = re.sub(
    r"# Initialize Supabase client.*?else:\n    print\(\"Supabase credentials not configured.*?\)\n",
    "",
    src,
    flags=re.DOTALL,
)

# Remove IS_PRODUCTION block at top
src = re.sub(
    r"IS_PRODUCTION = bool\([^)]+\)\n\n\n",
    "",
    src,
    flags=re.DOTALL,
)

# Simplify secret key
src = src.replace(
    """# Configuration
_secret = os.environ.get('SECRET_KEY')
if IS_PRODUCTION and not _secret:
    raise RuntimeError('SECRET_KEY environment variable is required in production')
app.config['SECRET_KEY'] = _secret or 'dev-secret-change-in-production'""",
    "app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'local-cms-dev-key')",
)

# DB always sqlite for CMS
src = re.sub(
    r"# Database configuration.*?app\.config\['SQLALCHEMY_TRACK_MODIFICATIONS'\].*?\n",
    """sqlite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'portfolio.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
print(f'CMS: SQLite at {sqlite_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

""",
    src,
    flags=re.DOTALL,
)

src = src.replace("app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION", "app.config['SESSION_COOKIE_SECURE'] = False")

# Remove CORS after_request entirely
src = re.sub(r"@app\.after_request\ndef add_cors_headers.*?return response\n\n", "", src, flags=re.DOTALL)

# Remove mail, login_manager blocks
src = re.sub(r"migrate = Migrate\(app, db\)\nmail = Mail\(app\)\n", "migrate = Migrate(app, db)\n", src)
src = re.sub(r"# Login Manager.*?return User\.query\.get\(int\(user_id\)\)\n\n", "", src, flags=re.DOTALL)
src = re.sub(r"def send_email\(.*?return False\n\n", "", src, flags=re.DOTALL)
src = re.sub(r"def send_verification_email\(.*?verification_url=verification_url\n    \)\n\n", "", src, flags=re.DOTALL)
src = re.sub(r"def send_password_reset_email\(.*?reset_url=reset_url\n    \)\n\n", "", src, flags=re.DOTALL)

# Admin creds - local only
src = re.sub(
    r"if IS_PRODUCTION:.*?ANALYTICS_PASSWORD = os\.environ\.get\('ANALYTICS_PASSWORD', 'kanalytics2026'\)\n",
    """ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'kepulia')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'kepulia123')
""",
    src,
    flags=re.DOTALL,
)

# project_detail without comments
src = src.replace(
    """    # Load comments from database - pass Comment objects directly to template
    comments = Comment.query.filter_by(project_id=project_id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Read description.txt""",
    "    # Read description.txt",
)
src = src.replace(
    "return render_template('project_detail.html', project=project, comments=comments, description=description)",
    "return render_template('project_detail.html', project=project, comments=[], description=description, cms_preview=True)",
)

# Header comment
header = '"""\nLocal CMS for static Cloudflare site.\nRun: python app.py  ->  http://127.0.0.1:5002/admin\nPublish: .\\publish.ps1\n"""\n\n'
if not src.startswith('"""'):
    src = header + src.lstrip()

(ROOT / "app.py").write_text(src, encoding="utf-8")
print("Wrote slim app.py")
