from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
db = SQLAlchemy(app)

with app.app_context():
    print('CWD:', os.getcwd())
    print('Database URL:', db.engine.url)
    print('Database file path:', db.engine.url.database)
    print('Absolute path:', os.path.abspath(db.engine.url.database) if db.engine.url.database else 'None')