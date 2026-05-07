@echo off
setlocal enabledelayedexpansion
title nexus-STARS-sync

echo.
echo  ========================================
echo   ⭐ nexus-STARS-sync — GitHub Stars Sync
echo  ========================================
echo.

:: Check for GITHUB_TOKEN
if "%GITHUB_TOKEN%"=="" (
    echo  [ERROR] GITHUB_TOKEN is not set.
    echo.
    echo  Set it in PowerShell:
    echo  [Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your_pat", "User")
    echo.
    goto :fail
)

:: Step 1: Sync stars
echo  [1/4] Syncing starred repos...
starred --username specimba --repository nexus-STARS-sync --sort --token %GITHUB_TOKEN%
if errorlevel 1 (
    echo  [ERROR] starred sync failed.
    goto :fail
)
echo  [OK] Stars synced.
echo.

:: Step 2: Pull latest (starred pushes to GitHub, not local)
echo  [2/4] Pulling latest from GitHub...
git pull --rebase origin main
if errorlevel 1 (
    echo  [WARN] Pull failed, continuing with local README.
)
echo.

:: Step 3: Beautify README
echo  [3/4] Beautifying README...
python scripts\beautify-stars.py --input README.md --force
if errorlevel 1 (
    echo  [ERROR] beautify-stars.py failed.
    goto :fail
)
echo  [OK] README beautified.
echo.

:: Step 4: Git commit & push
echo  [4/4] Committing and pushing...
git add README.md
git diff --cached --quiet
if not errorlevel 1 (
    echo  [SKIP] Nothing to commit.
) else (
    git commit -m "beautify: update stars README"
    if errorlevel 1 (
        echo  [ERROR] git commit failed.
        goto :fail
    )
    echo  [OK] Committed.
)

git push
if errorlevel 1 (
    echo  [ERROR] git push failed.
    goto :fail
)
echo  [OK] Pushed.
echo.
echo  ========================================
echo   ✅ Done! Check https://github.com/specimba/nexus-STARS-sync
echo  ========================================
pause
exit /b 0

:fail
echo.
echo  ========================================
echo   ❌ Sync failed. See errors above.
echo  ========================================
pause
exit /b 1
