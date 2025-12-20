# Project Portfolio Flask App

This project is a local-first portfolio website for uploading, managing, and displaying your projects. It is designed for easy migration to a cloud host (e.g., Cloudflare) in the future.

## File Storage Options

### Cloudinary (Default for small files)
- **Free tier**: 25GB storage, 25GB monthly bandwidth
- **File limit**: 10MB per file
- **Best for**: Images, small documents, optimized delivery

### Cloudflare R2 (Optional for large files)
- **Free tier**: 10GB storage, unlimited bandwidth
- **File limit**: No limit per file
- **Best for**: Large 3D models, ZIP files, unlimited downloads

#### Setting up Cloudflare R2:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/) → R2
2. Create a new bucket (e.g., `portfolio-files`)
3. Create an API token with Object Read & Write permissions
4. Update `.env` file with your credentials:
   ```
   CLOUDFLARE_R2_ACCESS_KEY=your_actual_access_key
   CLOUDFLARE_R2_SECRET_KEY=your_actual_secret_key
   CLOUDFLARE_R2_ACCOUNT_ID=your_account_id
   CLOUDFLARE_R2_BUCKET_NAME=portfolio-files
   ```
### Automatic File Routing

The app automatically chooses the best storage based on file size:

- **Files ≤10MB**: Cloudinary (optimized delivery, transformations)
- **Files >10MB with R2 configured**: Cloudflare R2 (unlimited size, cost-effective)
- **Files >10MB without R2**: Local storage (immediate access, no external costs)

## 3D Model Support

The app has special support for 3D models created with tools like SuperSplat Editor:

### Supported Formats
- **ZIP files**: Automatically extracted, HTML viewer embedded
- **Individual 3D files**: OBJ, STL, GLTF, GLB, FBX, DAE, 3DS
- **Word documents**: Text extracted and saved as description

### Upload Process
1. Upload ZIP file containing HTML, JS, CSS, and 3D assets
2. App extracts HTML content and saves to `viewer3D` field
3. All assets (>10MB go to R2, ≤10MB to Cloudinary)
4. URLs in HTML are automatically updated
5. 3D viewer displays directly on project page

### Storage Decision Logic
- Small assets (JS, CSS, small images): Cloudinary
- Large assets (PLY files, textures >10MB): Cloudflare R2 or local
- HTML content: Stored in database, assets served from CDN

## Getting Started
1. Install requirements: `pip install -r requirements.txt`
2. Run the app: `python app.py`
3. Access the site at `http://localhost:5001`

## Deployment
- To deploy online, upload the entire folder (including `projects/`) to your host (e.g., Cloudflare Pages with Python support).

## Security
- Only admin can upload/delete projects
- Comments are open to all (can be extended with moderation)

## Folder Structure
- `projects/` — all project subfolders
- `projects.json` — metadata for all projects
- `comments.json` — stores comments for each project

---

## Cloudinary vs Cloudflare R2 Comparison

| Feature | Cloudinary Free | Cloudflare R2 Free | Local Storage |
|---------|----------------|-------------------|---------------|
| Storage | 25GB | 10GB | Unlimited |
| File Size Limit | 10MB | No limit | No limit |
| Bandwidth | 25GB/month | Unlimited | Server limits |
| CDN | Global CDN | Cloudflare CDN | None |
| Cost for 200MB file | ~$0.09/month | ~$0.015/month | $0 |
| Image Optimization | Yes | No | No |
| API Complexity | Simple | AWS S3 compatible | None |

## Setting up Cloudflare R2 (Optional)

1. **Create Cloudflare Account**: Go to [cloudflare.com](https://cloudflare.com) and sign up
2. **Access R2**: In dashboard, go to R2 → Create bucket (name it `portfolio-files`)
3. **Create API Token**:
   - Go to R2 → Manage API Tokens → Create Token
   - Permissions: Object Read & Write
   - Copy the Access Key ID and Secret Access Key
4. **Get Account ID**: In dashboard, go to R2 → Your Account ID is shown at the top
5. **Configure Public Access** (Important!):
   - In R2 bucket settings, enable "Allow public access"
   - Or configure CORS for your domain
6. **Update .env file** with your credentials
7. **Test**: Upload a large file (>10MB) - it should go to R2 automatically

**Note**: R2 URLs will be in format: `https://{account-id}.r2.cloudflarestorage.com/{bucket}/{file}`

## User Monitoring & Analytics

The app includes a comprehensive user monitoring system using Supabase to track visitor behavior and analytics.

### Features Tracked
- **IP Address**: Real client IP (handles proxies/X-Forwarded-For)
- **Screen Resolution**: User's display resolution
- **User Agent**: Browser and device information
- **Page Visits**: All page views with timestamps
- **Session Tracking**: Unique session IDs for user journeys
- **Project Interactions**: Clicks on project cards
- **Referrer Data**: Where users came from

### Setup Supabase

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com) and create account
   - Create new project

2. **Run Database Schema**:
   - Go to SQL Editor in Supabase dashboard
   - Copy and run the contents of `supabase_schema.sql`

3. **Get API Keys**:
   - Go to Settings → API
   - Copy Project URL and anon/public key

4. **Configure Environment**:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

### Analytics Dashboard

Access the analytics dashboard at `/admin/analytics` (admin only):

- **Real-time Statistics**: Total visits, unique sessions, IPs
- **Popular Pages**: Most visited pages
- **Screen Resolutions**: Device screen sizes
- **Recent Activity**: Last 20 visits with details
- **Raw Data Export**: JSON data for further analysis

### Privacy & Compliance

- **Anonymous Tracking**: No personal data stored without consent
- **Session-based**: Uses anonymous session IDs
- **GDPR Compliant**: Can be disabled by removing Supabase config
- **Data Retention**: Configurable time periods (default: 30 days)

### Technical Details

- **Automatic Tracking**: JavaScript collects data on page load
- **API Endpoints**: `/api/track-visit` for data collection
- **Admin API**: `/api/analytics` for dashboard data
- **Database**: PostgreSQL with Row Level Security
- **Performance**: Asynchronous tracking, doesn't block page loads
