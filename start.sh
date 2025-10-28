#!/bin/bash
# Build script for Render.com

# Set environment variables
export FLASK_ENV=production

# Create necessary directories
mkdir -p projects
mkdir -p uploads
mkdir -p static/uploads

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start the application with gunicorn
echo "Starting Flask application..."
exec gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --timeout 120