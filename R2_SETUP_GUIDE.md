# Cloudflare R2 Setup Guide

## SSL Handshake Issue Resolution

You're experiencing SSL handshake failures when trying to connect to Cloudflare R2. This is typically caused by network restrictions or configuration issues.

## Step-by-Step Setup Checklist

### 1. Access Cloudflare Dashboard
- Go to https://dash.cloudflare.com/
- Sign in to your account

### 2. Navigate to R2
- Click on "R2" in the sidebar

### 3. Check/Create Bucket
- Look for a bucket named "portfolio-files"
- If it doesn't exist, click "Create bucket"
- Name it: `portfolio-files`

### 4. Configure Bucket Permissions
- Click on the "portfolio-files" bucket
- Go to "Settings" tab
- Under "Public Access", toggle it ON
- This allows public read access to files

### 5. Create API Token
- Go back to R2 overview page
- Click "Manage API tokens" (or "Create token" if none exist)
- Click "Create API token"
- Set permissions:
  - **Object Read & Write** (required)
- Set token name: "Portfolio Upload Token"
- Click "Create Token"

### 6. Get Credentials
- Copy the following values:
  - **Account ID**: (shown at the top)
  - **Access Key ID**: (from the token)
  - **Secret Access Key**: (from the token - keep this secret!)

### 7. Update .env File
Update your `.env` file with the correct values:

```
CLOUDFLARE_R2_ACCESS_KEY=your_actual_access_key_here
CLOUDFLARE_R2_SECRET_KEY=your_actual_secret_key_here
CLOUDFLARE_R2_ACCOUNT_ID=your_actual_account_id_here
```

### 8. Test the Connection
After updating the credentials, restart your Flask app and try uploading a ZIP file.

## If SSL Issues Persist

If you still get SSL handshake failures:

1. **Check Network/Firewall**: Your network might be blocking Cloudflare connections
2. **Try Different Network**: Test from a different WiFi or mobile data
3. **VPN**: Try using a VPN service
4. **Contact ISP**: Some ISPs block certain CDNs

## Alternative: Use Cloudinary Fallback

If R2 continues to have issues, the app will automatically fall back to using Cloudinary for file uploads (with the 10MB limit).

## Testing Your Setup

Once configured, you can test by:
1. Going to your admin upload page
2. Selecting a ZIP file with 3D model content
3. Clicking upload
4. Checking if files appear in your Cloudflare R2 bucket</content>
<parameter name="filePath">c:\Users\ATA\Desktop\saitis gashveba\4.1_zapasi_axal_saitamde\R2_SETUP_GUIDE.md