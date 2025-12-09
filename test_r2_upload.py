#!/usr/bin/env python3
"""
Test script to verify Cloudflare R2 upload functionality
"""

import os
import boto3
from dotenv import load_dotenv
import zipfile
import tempfile
import io
from botocore.config import Config

# Load environment variables
load_dotenv()

def test_r2_connection():
    """Test R2 connection and basic operations"""

    print("=== CLOUDFLARE R2 CONNECTION TEST ===")
    print()

    # R2 credentials
    account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
    access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
    secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
    bucket_name = os.environ.get('CLOUDFLARE_R2_BUCKET_NAME', 'portfolio-files')

    print(f"Account ID: {account_id}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {access_key[:10]}..." if access_key else "No access key")
    print()

    if not all([account_id, access_key, secret_key]):
        print("❌ Missing R2 credentials")
        return False

    try:
        # Create R2 client
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4', use_ssl=False)
        )

        print("✅ R2 client created successfully")

        # Test connection by listing objects
        try:
            response = r2_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            objects = response.get('Contents', [])
            print(f"✅ Bucket access successful. Found {len(objects)} objects")
            if objects:
                print("Sample objects:")
                for obj in objects[:3]:
                    print(f"  - {obj['Key']}")
            print()
        except Exception as e:
            print(f"⚠️  Could not list bucket contents: {e}")
            print("This might be normal if bucket is empty or permissions are restricted")
            print()

        # Test upload with a simple text file
        test_key = 'test-connection.txt'
        test_content = b'R2 connection test - ' + str(os.urandom(8)).encode()

        try:
            r2_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            print(f"✅ Test upload successful: {test_key}")

            # Generate public URL
            public_url = f'https://pub-{account_id}.r2.dev/{test_key}'
            print(f"📎 Public URL: {public_url}")
            print()

        except Exception as e:
            print(f"❌ Test upload failed: {e}")
            return False

        print("🎉 R2 integration test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ R2 client creation failed: {e}")
        return False

def test_zip_processing():
    """Test ZIP file processing logic"""

    print("=== ZIP PROCESSING TEST ===")
    print()

    # Create a temporary ZIP file with some test content
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = tmp_zip.name

    try:
        # Create test ZIP with HTML and assets
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add HTML file
            html_content = '''<!DOCTYPE html>
<html>
<head><title>Test 3D Model</title></head>
<body>
    <h1>Test 3D Viewer</h1>
    <script src="script.js"></script>
    <link rel="stylesheet" href="style.css">
</body>
</html>'''
            zf.writestr('index.html', html_content)

            # Add JS file
            js_content = 'console.log("Test script loaded");'
            zf.writestr('script.js', js_content)

            # Add CSS file
            css_content = 'body { background: #f0f0f0; }'
            zf.writestr('style.css', css_content)

            # Add file in subdirectory
            zf.writestr('assets/model.obj', '# Test OBJ file')

        print(f"✅ Created test ZIP: {zip_path}")

        # Test extraction and processing
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"📁 ZIP contents ({len(file_list)} files):")
            for filename in file_list:
                print(f"  - {filename}")
            print()

            # Find HTML file
            html_files = [f for f in file_list if f.lower().endswith('.html')]
            if html_files:
                html_file = html_files[0]
                print(f"🎯 Found HTML file: {html_file}")

                # Read HTML content
                with zf.open(html_file) as f:
                    content = f.read().decode('utf-8')
                    print("📄 HTML content preview:")
                    print(content[:200] + "..." if len(content) > 200 else content)
                    print()

                # Simulate folder structure preservation
                base_path = os.path.dirname(html_file) if os.path.dirname(html_file) else ''
                print(f"📂 Base path for assets: '{base_path}'")

                # Check for relative paths in HTML
                import re
                relative_paths = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)
                print("🔗 Relative paths found in HTML:")
                for path in relative_paths:
                    if not path.startswith(('http://', 'https://', '//')):
                        full_path = os.path.join(base_path, path).replace('\\', '/')
                        print(f"  - {path} → {full_path}")
                print()

        print("✅ ZIP processing test completed!")
        return True

    except Exception as e:
        print(f"❌ ZIP processing test failed: {e}")
        return False

    finally:
        # Clean up
        if os.path.exists(zip_path):
            os.unlink(zip_path)

if __name__ == '__main__':
    print("🧪 Starting R2 Integration Tests")
    print("=" * 50)
    print()

    r2_ok = test_r2_connection()
    print()
    zip_ok = test_zip_processing()
    print()

    if r2_ok and zip_ok:
        print("🎉 All tests passed! R2 integration should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    print()
    print("Next steps:")
    print("1. Upload a real 3D model ZIP file through the web interface")
    print("2. Check that files are uploaded to R2 with correct folder structure")
    print("3. Verify the 3D viewer loads correctly in the iframe")