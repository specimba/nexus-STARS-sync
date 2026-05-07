#Requires -Version 5.1
<#
.SYNOPSIS
    nexus-STARS-sync — sync GitHub stars, beautify README, push to repo.
.PARAMETER Username
    GitHub username (default: specimba)
.PARAMETER Repository
    Target repository name (default: nexus-STARS-sync)
.PARAMETER CommitMessage
    Git commit message (default: "beautify: update stars README")
.EXAMPLE
    .\sync.ps1
    .\sync.ps1 -Username "myuser" -Repository "mystars"
#>
param(
    [string]$Username = "specimba",
    [string]$Repository = "nexus-STARS-sync",
    [string]$CommitMessage = "beautify: update stars README"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host "  ⭐ nexus-STARS-sync — GitHub Stars Sync" -ForegroundColor Yellow
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""

# --- Prerequisite checks ---
if (-not $env:GITHUB_TOKEN) {
    Write-Host "  [ERROR] GITHUB_TOKEN is not set." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Set it permanently:" -ForegroundColor Gray
    Write-Host '  [Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your_pat", "User")' -ForegroundColor Gray
    exit 1
}

if (-not (Get-Command starred -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] 'starred' not found. Install it:" -ForegroundColor Red
    Write-Host "  pip install starred" -ForegroundColor Gray
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$beautifier = Join-Path $scriptDir "beautify-stars.py"
if (-not (Test-Path $beautifier)) {
    Write-Host "  [ERROR] beautify-stars.py not found at: $beautifier" -ForegroundColor Red
    exit 1
}

# --- Step 1: Sync stars ---
Write-Host "  [1/4] Syncing starred repos..." -ForegroundColor Cyan
try {
    starred --username $Username --repository $Repository --sort --token $env:GITHUB_TOKEN
    Write-Host "  [OK] Stars synced." -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] starred sync failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# --- Step 2: Pull latest ---
Write-Host "  [2/4] Pulling latest from GitHub..." -ForegroundColor Cyan
try {
    git pull --rebase origin main 2>&1 | Out-Null
    Write-Host "  [OK] Pulled." -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Pull failed, continuing with local README." -ForegroundColor Yellow
}
Write-Host ""

# --- Step 3: Beautify README ---
Write-Host "  [3/4] Beautifying README..." -ForegroundColor Cyan
try {
    python $beautifier --input "README.md" --force
    Write-Host "  [OK] README beautified." -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] beautify-stars.py failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# --- Step 4: Git commit & push ---
Write-Host "  [4/4] Committing and pushing..." -ForegroundColor Cyan
git add README.md
$diff = git diff --cached --quiet 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [SKIP] Nothing to commit." -ForegroundColor Yellow
} else {
    try {
        git commit -m $CommitMessage
        Write-Host "  [OK] Committed." -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] git commit failed: $_" -ForegroundColor Red
        exit 1
    }
}

try {
    git push
    Write-Host "  [OK] Pushed." -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] git push failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host "  ✅ Done! Check https://github.com/$Username/$Repository" -ForegroundColor Green
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""
