@echo off
title Mikasa AI v7.0.0 Launcher
cd /d "%~dp0"
echo ========================================================
echo   MIKASA AI v7.0.0 — Ishga tushirilmoqda...
echo ========================================================

REM 1. Orqa fonda Python backend xizmati mavjudligini tekshirish
powershell -NoProfile -Command "$conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 18420 -WarningAction SilentlyContinue -InformationLevel Quiet; if (-not $conn) { Write-Host 'Python Backend ishga tushirilmoqda (127.0.0.1:18420)...' -ForegroundColor Cyan; $py = '..\..\.venv\Scripts\python.exe'; if (Test-Path $py) { Start-Process -FilePath $py -ArgumentList '..\..\core\api_server.py' -WindowStyle Hidden } else { python ..\..\core\api_server.py } Start-Sleep -Seconds 1 }"

REM 2. Desktop ilovani ochish
start "" "Mikasa-AI-v7.0.0.exe"
