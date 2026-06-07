#!/usr/bin/env python3
"""
Test Cloudflare R2 connection and bucket access
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
import os
from dotenv import load_dotenv

load_dotenv()

def test_r2_connection():
    print("=== CLOUDFLARE R2 CONNECTION TEST ===")
    print()

    # Get credentials
    access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
    secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
    account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
    bucket_name = 'portfolio-files'

    print(f"Account ID: {account_id}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {access_key[:10]}..." if access_key else "No access key")
    print()

    if not all([access_key, secret_key, account_id]):
        print("❌ Missing R2 credentials")
        return False

    try:
        # Create client
        client = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4', region_name='auto')
        )

        print("✅ R2 client created successfully")

        # Test 1: Check if bucket exists
        try:
            client.head_bucket(Bucket=bucket_name)
            print("✅ Bucket exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print("❌ Bucket does not exist")
                print(f"   Please create a bucket named '{bucket_name}' in your Cloudflare R2 dashboard")
                return False
            elif error_code == '403':
                print("❌ Access denied to bucket")
                print("   Check your API token permissions")
                return False
            else:
                print(f"❌ Bucket check failed: {error_code} - {e.response['Error']['Message']}")
                return False

        # Test 2: Try to list objects
        try:
            response = client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            objects = response.get('Contents', [])
            print(f"✅ Can list bucket contents. Found {len(objects)} objects")
        except ClientError as e:
            print(f"⚠️  Cannot list bucket contents: {e.response['Error']['Message']}")
            print("   This might be normal if bucket is empty")

        # Test 3: Try a simple upload
        try:
            test_key = 'connection_test.txt'
            test_content = b'R2 connection test - ' + str(os.urandom(8)).hex().encode()

            client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )
            print("✅ Test upload successful")

            # Generate public URL
            public_url = f'https://pub-{account_id}.r2.dev/{test_key}'
            print(f"📎 Test file URL: {public_url}")

            # Test 4: Try to access the uploaded file
            try:
                response = client.get_object(Bucket=bucket_name, Key=test_key)
                retrieved_content = response['Body'].read()
                if retrieved_content == test_content:
                    print("✅ File retrieval successful")
                else:
                    print("⚠️  File retrieval returned different content")
            except ClientError as e:
                print(f"⚠️  Cannot retrieve uploaded file: {e.response['Error']['Message']}")

        except ClientError as e:
            print(f"❌ Test upload failed: {e.response['Error']['Message']}")
            return False
        except EndpointConnectionError as e:
            print(f"❌ Connection failed: {e}")
            print("   Check your internet connection and firewall settings")
            return False

        print()
        print("🎉 R2 connection test completed successfully!")
        print("Your R2 setup appears to be working correctly.")
        return True

    except NoCredentialsError:
        print("❌ No credentials provided")
        return False
    except EndpointConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("   Check your internet connection and firewall settings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_r2_connection()

    if not success:
        print()
        print("=== TROUBLESHOOTING STEPS ===")
        print("1. Go to https://dash.cloudflare.com/ and navigate to R2")
        print("2. Create a bucket named 'portfolio-files'")
        print("3. Create an API token with 'Object Read & Write' permissions")
        print("4. Make sure the bucket is set to 'Public' access")
        print("5. Update your .env file with the correct credentials")
        print("6. Check your internet connection and firewall settings")