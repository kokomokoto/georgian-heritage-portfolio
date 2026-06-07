import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
account_id = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID')
bucket_name = 'portfolio-files'

print('Testing basic R2 connection...')

try:
    client = boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4', region_name='auto', verify=False)
    )

    # Try to create bucket first
    try:
        client.create_bucket(Bucket=bucket_name)
        print('✅ Bucket created successfully')
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
            print('✅ Bucket already exists')
        else:
            print(f'❌ Bucket creation failed: {e.response["Error"]["Message"]}')

    # Try simple upload
    client.put_object(
        Bucket=bucket_name,
        Key='test.txt',
        Body=b'Hello World',
        ContentType='text/plain'
    )
    print('✅ Upload successful')

    # Generate public URL
    public_url = f'https://pub-{account_id}.r2.dev/test.txt'
    print(f'📎 Test file URL: {public_url}')

except Exception as e:
    print(f'❌ Error: {e}')
    print('This indicates a problem with your R2 setup.')
    print('Possible issues:')
    print('1. Invalid credentials')
    print('2. Bucket permissions')
    print('3. Network/firewall blocking R2')
    print('4. Account ID is incorrect')