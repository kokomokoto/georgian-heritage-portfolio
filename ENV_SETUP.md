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
# Local dev example (SQLite)
DATABASE_URL=sqlite:///portfolio.db

# Production (Render) example (PostgreSQL)
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Email Settings (Gmail SMTP)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password

# Google Analytics 4 (optional)
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Internal analytics dashboard window (days). Default: 30
ANALYTICS_DAYS=30

# Supabase (optional; legacy analytics store)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
# Recommended for server-side read/merge/migration (bypasses RLS):
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
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

## Production Verification (GA / Deploy)

Deploy-ის დადასტურებისთვის (და რომ სწორ ფაილს/commit-ს უშვებს Render), გამოყენებულია ეს debug endpoint-ები:

- `GET /health` → მარტივი health check (`mode`: `full_app` ან `emergency_recovery`)
- `GET /api/version` → აბრუნებს `mode`, `ga_configured`, `ga_measurement_id` (mask-ით) და `git_commit` (თუ Render აძლევს env-ში)
- `GET /api/ga-status` → GA4 Measurement ID კონფიგურაციის სწრაფი შემოწმება

თუ ამ endpoint-ებზე ყველგან 404 მოდის, ეს თითქმის ყოველთვის ნიშნავს ერთ-ერთს:
- Render არ დ deploy-და ბოლო commit-ზე (Deploy/Logs-ში შეამოწმე)
- Start Command სხვა entrypoint-ს უშვებს (მაგ: სხვა module)
- Custom domain არ არის მიბმული იმ Render service-ზე