# Publish local CMS changes to Cloudflare Pages static repo
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== 1. Export projects to _cloudflare_static ===" -ForegroundColor Cyan
$env:PYTHONUTF8 = "1"
python export_to_static.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$staticDir = Join-Path $PSScriptRoot "_cloudflare_static"
if (-not (Test-Path $staticDir)) {
    Write-Host "ERROR: _cloudflare_static folder not found." -ForegroundColor Red
    Write-Host "Clone your Cloudflare Pages repo into _cloudflare_static/ first."
    exit 1
}

if (-not (Test-Path (Join-Path $staticDir ".git"))) {
    Write-Host ""
    Write-Host "Export done. Copy projects_data.js to your Cloudflare git repo manually." -ForegroundColor Yellow
    Write-Host "Path: $staticDir\projects_data.js"
    exit 0
}

Write-Host ""
Write-Host "=== 2. Git push from _cloudflare_static ===" -ForegroundColor Cyan
Push-Location $staticDir
git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "No changes to commit." -ForegroundColor Yellow
    Pop-Location
    exit 0
}
$msg = "Update projects " + (Get-Date -Format "yyyy-MM-dd HH:mm")
git commit -m $msg
git push
Pop-Location
Write-Host ""
Write-Host "Done. Cloudflare Pages will deploy shortly." -ForegroundColor Green
