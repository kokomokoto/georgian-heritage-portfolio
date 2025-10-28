# Project Portfolio Flask App

This project is a local-first portfolio website for uploading, managing, and displaying your projects. It is designed for easy migration to a cloud host (e.g., Cloudflare) in the future.

## Features
- Admin authentication for uploading and deleting projects
- Projects stored as subfolders in the `projects/` directory
- Each project contains: title, description (Word), main image, other images, 3D HTML or link
- All project metadata is aggregated in `projects.json`
- Users can search projects by title
- Project detail page shows title, 3D viewer, description, images, and comments
- Comments can be added by any visitor

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

Replace placeholder files as needed. For questions, see the code comments or contact the author.
