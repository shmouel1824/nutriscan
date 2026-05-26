@echo off
REM ═══════════════════════════════════════════════
REM  NutriScan — Auto Git Push
REM  Usage: push "your commit message"
REM ═══════════════════════════════════════════════

if "%~1"=="" (
    echo.
    echo  Usage: push "your commit message"
    echo  Example: push "added bilingual support"
    echo.
    pause
    exit /b 1
)

echo.
echo  NutriScan — Pushing to GitHub...
echo  Commit: %~1
echo.

git add .
git commit -m "%~1"
git push origin main

echo.
echo  Done! Check: https://github.com/shmouel1824/nutriscan
echo.