@echo off
title Mikasa AI 7.0 Desktop
echo ===================================================
echo   MIKASA AI 7.0 — DESKTOP ISHCHI STOLI ILOVASI
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/2] Frontend tekshirilmoqda...
start /B npm run dev > nul 2>&1

timeout /t 2 /nobreak > nul

echo [2/2] Mikasa AI 7.0 Desktop oynasi ochilmoqda...

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="http://localhost:1420" --window-size=1280,800 --app-id=mikasa-ai-7
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="http://localhost:1420" --window-size=1280,800
) else (
    start http://localhost:1420
)

echo.
echo Mikasa AI 7.0 Desktop oynasi muvaffaqiyatli ishga tushdi!
echo.
