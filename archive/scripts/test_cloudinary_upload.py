#!/usr/bin/env python3
"""
Debug script to test Cloudinary upload functionality
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import time

# Load environment variables
load_dotenv()

def test_cloudinary_upload():
    """Test Cloudinary upload with a sample file"""
    
    print("=== CLOUDINARY UPLOAD TEST ===")
    print()
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
    
    # Check configuration
    config = cloudinary.config()
    print(f"Cloud name: {config.cloud_name}")
    print(f"API key: {config.api_key[:10]}..." if config.api_key else "No API key")
    print()
    
    # Test basic connection
    try:
        result = cloudinary.api.ping()
        print("Connection test: SUCCESS")
        print(f"Status: {result}")
        print()
        
        # Check usage/limits
        try:
            usage = cloudinary.api.usage()
            print("Cloudinary Usage Info:")
            print(f"Plan: {usage.get('plan', 'Unknown')}")
            print(f"Monthly Credits: {usage.get('credits', {}).get('usage', 'Unknown')}/{usage.get('credits', {}).get('limit', 'Unknown')}")
            print(f"Storage: {usage.get('storage', {}).get('usage', 'Unknown')}/{usage.get('storage', {}).get('limit', 'Unknown')}")
            print()
        except Exception as e:
            print(f"Usage check failed: {e}")
            print()
            
    except Exception as e:
        print(f"Connection test: FAILED - {e}")
        return
    
    # Test file upload simulation
    print("Testing upload process...")
    
    # Create a test file path (you can change this to an actual image file)
    test_files = [
        "test_image.jpg",
        "test.png", 
        "sample.jpeg"
    ]
    
    # Find an existing image file or create a dummy one
    test_file = None
    for filename in test_files:
        if os.path.exists(filename):
            test_file = filename
            break
    
    if not test_file:
        # Create a simple test file
        print("Creating test file...")
        test_file = "test_upload.txt"
        with open(test_file, 'w') as f:
            f.write("Test file for Cloudinary upload")
    
    print(f"Using test file: {test_file}")
    
    # Simulate the upload process from your app
    try:
        with open(test_file, 'rb') as file_data:
            print("Attempting upload...")
            upload_result = cloudinary.uploader.upload(
                file_data,
                folder="comments",
                public_id=f"comment_{int(time.time())}_{secure_filename(test_file)}"
            )
            
            media_url = upload_result['secure_url']
            print(f"Upload SUCCESS!")
            print(f"URL: {media_url}")
            print(f"Public ID: {upload_result.get('public_id')}")
            print(f"Format: {upload_result.get('format')}")
            
    except Exception as e:
        print(f"Upload FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check common issues
        if "Invalid API key" in str(e):
            print("ISSUE: API key is invalid")
        elif "cloud_name" in str(e):
            print("ISSUE: Cloud name is invalid")
        elif "signature" in str(e):
            print("ISSUE: API secret is invalid")
        else:
            print("ISSUE: Other error")
    
    # Cleanup test file if we created it
    if test_file == "test_upload.txt" and os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_cloudinary_upload()