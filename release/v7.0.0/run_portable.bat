@echo off
title Mikasa AI v7.0.0 Launcher
cd /d "%~dp0"
echo ========================================================
echo   MIKASA AI v7.0.0 — Ishga tushirilmoqda...
echo ========================================================

REM 1. Orqa fonda Python backend xizmati mavjudligini tekshirish
powershell -NoProfile -Command "$conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 18420 -WarningAction SilentlyContinue -InformationLevel Quiet; if (-not $conn) { Write-Host 'Python Backend ishga tushirilmoqda (127.0.0.1:18420)...' -ForegroundColor Cyan; $py1 = '..\..\..\.venv\Scripts\python.exe'; $py2 = '..\..\.venv\Scripts\python.exe'; $workDir = (Resolve-Path '..\..').Path; if (Test-Path $py1) { Start-Process -FilePath (Resolve-Path $py1).Path -ArgumentList 'core\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } elseif (Test-Path $py2) { Start-Process -FilePath (Resolve-Path $py2).Path -ArgumentList 'core\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } else { Start-Process -FilePath 'python' -ArgumentList 'core\api_server.py' -WorkingDirectory $workDir -WindowStyle Hidden } Start-Sleep -Seconds 2 }"

REM 2. Desktop ilovani ochish
start "" "Mikasa-AI-v7.0.0.exe"
