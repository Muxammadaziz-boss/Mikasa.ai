@echo off
title Misa AI 9.0 Desktop
echo ===================================================
echo    MISA AI 9.0 - DESKTOP ISHCHI STOLI ILOVASI
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/2] Frontend tekshirilmoqda...
start /B cmd /c "npm run dev" > nul 2>&1

rem Kutish (2 soniya)
ping 127.0.0.1 -n 3 > nul

echo [2/2] Misa AI 9.0 Desktop oynasi ochilmoqda...

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
set EDGE="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if exist %CHROME% (
    start "" %CHROME% --app="http://localhost:1420" --window-size=1280,800 --app-id=misa-ai-9
) else if exist %EDGE% (
    start "" %EDGE% --app="http://localhost:1420" --window-size=1280,800
) else (
    start http://localhost:1420
)

echo.
echo Misa AI 9.0 Desktop oynasi muvaffaqiyatli ochildi!
echo.
