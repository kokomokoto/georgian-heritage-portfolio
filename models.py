from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Comments relationship
    comments = db.relationship('Comment', backref='author', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def generate_reset_token(self):
        """Generate password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token"""
        return (self.reset_token == token and 
                self.reset_token_expires and 
                self.reset_token_expires > datetime.utcnow())
    
    def __repr__(self):
        return f'<User {self.email}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Required for registered users only
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    media_urls = db.Column(db.Text, nullable=True)  # JSON array of Cloudinary URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Replies relationship
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Likes relationship
    likes = db.relationship('Like', backref='comment', lazy=True, cascade='all, delete-orphan')
    
    def get_like_count(self):
        return len(self.likes)
    
    def is_liked_by_user(self, user_id):
        return any(like.user_id == user_id for like in self.likes)
    
    def get_media_urls(self):
        """Get media URLs as a list - with backwards compatibility"""
        if self.media_urls:
            import json
            try:
                return json.loads(self.media_urls)
            except json.JSONDecodeError:
                return []
        # Backwards compatibility: check if old media_url field exists
        elif hasattr(self, 'media_url') and self.media_url:
            return [self.media_url]
        return []
    
    def set_media_urls(self, urls_list):
        """Set media URLs from a list"""
        if urls_list:
            import json
            self.media_urls = json.dumps(urls_list)
        else:
            self.media_urls = None
    
    def has_media(self):
        """Check if comment has any media files - with backwards compatibility"""
        # Check new format first
        if self.media_urls:
            return bool(self.get_media_urls())
        # Check old format
        elif hasattr(self, 'media_url') and self.media_url:
            return True
        return False
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='user_likes')
    
    # Ensure one like per user per comment
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),)

class Project(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    main_image = db.Column(db.Text, nullable=True)
    main_image_caption = db.Column(db.String(200), nullable=True)  # Caption for main image
    other_images = db.Column(db.Text, nullable=True)  # JSON array
    model_urls = db.Column(db.Text, nullable=True)  # JSON array for 3D model URLs
    viewer3D = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    description_file = db.Column(db.String(100), nullable=True)
    folder = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.String(50), nullable=True)
    documents = db.Column(db.Text, nullable=True)  # JSON array
    loading_video = db.Column(db.Text, nullable=True)
    loading_audio = db.Column(db.Text, nullable=True)
    project_info = db.Column(db.Text, nullable=True)  # JSON object
    type_categories = db.Column(db.Text, nullable=True)  # JSON array
    period_categories = db.Column(db.Text, nullable=True)  # JSON array
    sort_order = db.Column(db.Integer, default=0)  # For manual ordering
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Project {self.title}>'