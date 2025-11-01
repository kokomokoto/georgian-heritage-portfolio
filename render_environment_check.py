#!/usr/bin/env python3
"""
Render.com Environment Check Script
This script helps verify all required environment variables are set
"""

import os

def check_render_environment():
    """Check if all required environment variables are set for Render.com"""
    
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection string',
        'SECRET_KEY': 'Flask secret key',
        'CLOUDINARY_CLOUD_NAME': 'Cloudinary cloud name',
        'CLOUDINARY_API_KEY': 'Cloudinary API key', 
        'CLOUDINARY_API_SECRET': 'Cloudinary API secret',
        'MAIL_USERNAME': 'Email username for notifications',
        'MAIL_PASSWORD': 'Email password for notifications'
    }
    
    print("🔍 Checking Render.com Environment Variables...")
    print("=" * 50)
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var:
                display_value = '***' + value[-3:] if len(value) > 3 else '***'
            elif 'KEY' in var:
                display_value = value[:8] + '...' if len(value) > 8 else value
            else:
                display_value = value[:20] + '...' if len(value) > 20 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MISSING - {description}")
            missing_vars.append(var)
    
    print("=" * 50)
    
    if missing_vars:
        print(f"❌ Found {len(missing_vars)} missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}: {required_vars[var]}")
        print("\n🚨 Add these variables in Render.com Dashboard:")
        print("   Settings > Environment > Add Environment Variable")
        return False
    else:
        print("✅ All environment variables are set!")
        return True

def generate_render_deployment_fix():
    """Generate commands to fix common Render.com deployment issues"""
    
    print("\n🔧 Render.com Deployment Fix Commands:")
    print("=" * 50)
    print("1. In Render.com Dashboard:")
    print("   - Go to your service")
    print("   - Click 'Settings' tab")
    print("   - Scroll to 'Environment Variables'")
    print("   - Add missing variables listed above")
    print("")
    print("2. Force redeploy:")
    print("   - Go to 'Manual Deploy' section")
    print("   - Click 'Deploy latest commit'")
    print("")
    print("3. Check build logs:")
    print("   - Go to 'Logs' tab")
    print("   - Look for any error messages during startup")
    print("")
    print("4. Database migration fix:")
    print("   - Add environment variable: FLASK_ENV=production")
    print("   - Add environment variable: DATABASE_MIGRATION=true")

if __name__ == '__main__':
    print("🚀 Render.com Environment & Deployment Checker")
    print("")
    
    # Check environment
    env_ok = check_render_environment()
    
    # Generate fix commands
    generate_render_deployment_fix()
    
    print("\n📋 Quick Fix Steps:")
    print("1. Set missing environment variables in Render dashboard")
    print("2. Redeploy the service") 
    print("3. Check logs for any remaining errors")
    print("4. Test the website functionality")