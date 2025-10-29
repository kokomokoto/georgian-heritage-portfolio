# 🔒 Environment Variables Setup

**IMPORTANT SECURITY NOTE:** Never commit .env files to Git!

## Required Environment Variables

Create a `.env` file in the project root with these variables:

```env
# Flask Settings
SECRET_KEY=your-strong-secret-key-here
FLASK_ENV=development

# Cloudinary Settings (Get from https://cloudinary.com)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key  
CLOUDINARY_API_SECRET=your-api-secret

# Database Settings
DATABASE_URL=sqlite:///portfolio.db

# Email Settings (Gmail SMTP)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

## Cloudinary Setup

1. Go to https://cloudinary.com
2. Create account / Login
3. Go to Dashboard
4. Copy your Cloud Name, API Key, and API Secret
5. Add them to your `.env` file

## Gmail Setup

1. Enable 2-Factor Authentication in Gmail
2. Generate App Password in Gmail Settings
3. Use the App Password (not your regular password) in `.env`

## Security

- ✅ `.env` is in `.gitignore` 
- ✅ Never commit sensitive data
- ✅ Use environment variables for all secrets
- ✅ Rotate API keys if exposed