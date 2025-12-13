"""
Minimal Flask App for Emergency Recovery
=========================================

This is a minimal version of the portfolio app used for emergency recovery.
It provides basic functionality to get the site back online quickly.
"""

from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emergency-recovery-key')

@app.route('/')
def home():
    """Basic home page for emergency recovery"""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio - Emergency Recovery Mode</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            p {
                color: #666;
                line-height: 1.6;
            }
            .status {
                background: #e8f5e8;
                border: 1px solid #4CAF50;
                color: #2E7D32;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Emergency Recovery Mode</h1>
            <div class="status">
                <strong>Status:</strong> Site is running in minimal recovery mode
            </div>
            <p>
                The portfolio site is currently running in emergency recovery mode.
                Full functionality will be restored shortly.
            </p>
            <p>
                If you're seeing this page, the basic Flask application is working correctly.
                The main application should be restored soon.
            </p>
            <p>
                <em>Last updated: Emergency Recovery Deployment</em>
            </p>
        </div>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'mode': 'emergency_recovery'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)