from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Project(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    main_image = db.Column(db.Text, nullable=True)
    main_image_caption = db.Column(db.String(200), nullable=True)
    other_images = db.Column(db.Text, nullable=True)
    model_urls = db.Column(db.Text, nullable=True)
    viewer3D = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    description_file = db.Column(db.String(100), nullable=True)
    folder = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.String(50), nullable=True)
    documents = db.Column(db.Text, nullable=True)
    loading_video = db.Column(db.Text, nullable=True)
    loading_audio = db.Column(db.Text, nullable=True)
    project_info = db.Column(db.Text, nullable=True)
    type_categories = db.Column(db.Text, nullable=True)
    period_categories = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Project {self.title}>'


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SiteSetting {self.key}>'
