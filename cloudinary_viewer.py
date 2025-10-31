#!/usr/bin/env python3
"""
Cloudinary სურათების სია
ყველა ატვირთული სურათის ნახვა
"""

import cloudinary
import cloudinary.api
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

def list_cloudinary_images():
    print("🌩️ CLOUDINARY MEDIA LIBRARY")
    print("=" * 50)
    
    try:
        # Get all images in comments folder
        result = cloudinary.api.resources(
            type="upload",
            prefix="comments/",
            max_results=100
        )
        
        print(f"📊 სულ სურათები: {len(result['resources'])}")
        print()
        
        for i, resource in enumerate(result['resources'], 1):
            print(f"🖼️  {i}. {resource['public_id']}")
            print(f"   📏 ზომა: {resource['width']}x{resource['height']}")
            print(f"   📁 ზომა: {resource['bytes']} bytes")
            print(f"   🌐 URL: {resource['secure_url']}")
            print(f"   📅 თარიღი: {resource['created_at']}")
            print()
            
    except Exception as e:
        print(f"❌ შეცდომა: {e}")
        print("🔧 შეამოწმე Cloudinary კონფიგურაცია .env ფაილში")

if __name__ == '__main__':
    list_cloudinary_images()