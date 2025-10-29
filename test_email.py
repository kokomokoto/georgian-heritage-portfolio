from app import app, db, User, send_password_reset_email
import os

# Run the test in application context
with app.app_context():
    # Check environment variables
    print(f"Mail username: {os.environ.get('MAIL_USERNAME')}")
    print(f"Mail password: {'*' * len(os.environ.get('MAIL_PASSWORD', '')) if os.environ.get('MAIL_PASSWORD') else 'Not set'}")
    
    # Check app config
    print(f"App MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"App MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', '')) if app.config.get('MAIL_PASSWORD') else 'Not set'}")
    
    # Find user
    user = User.query.filter_by(email='alambarimalambari@gmail.com').first()
    
    if user:
        print(f"User found: {user.email}")
        print(f"User verified: {user.email_verified}")
        
        # Generate reset token to see if that works
        token = user.generate_reset_token()
        print(f"Generated token: {token[:20]}...")
        
        # Try to send password reset email
        try:
            result = send_password_reset_email(user)
            print(f"Email sent result: {result}")
        except Exception as e:
            print(f"Error sending email: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("User not found")