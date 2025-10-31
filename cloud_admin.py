#!/usr/bin/env python3
"""
Admin panel for viewing online database
ღრუბლოვანი ბაზის ნახვა ადმინ პანელიდან
"""

from flask import render_template, request, redirect, url_for, session, flash
from app import app, db
from models import User, Comment, Like
import os

@app.route('/cloud-admin', methods=['GET', 'POST'])
def cloud_admin():
    """Admin panel for viewing cloud database"""
    
    # Simple password protection
    if request.method == 'POST':
        password = request.form.get('password')
        # Change this to your admin password
        if password == 'admin123':  # Change this!
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

if __name__ == "__main__":
    print("Cloud admin routes added!")
    print("Access at: /cloud-admin")