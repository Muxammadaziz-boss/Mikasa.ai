# Mikasa AI 7.0 Desktop Launcher (PowerShell)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   MIKASA AI 7.0 - DESKTOP ISHCHI STOLI ILOVASI    " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Start dev server in background if not already running
$conn = Get-NetTCPConnection -LocalPort 1420 -ErrorAction SilentlyContinue
if (-not $conn) {
    Write-Host "[1/2] Frontend serveri ishga tushirilmoqda..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/2] Frontend serveri allaqachon faol (Port 1420)." -ForegroundColor Green
}

# 2. Launch in native standalone desktop window mode
Write-Host "[2/2] Mikasa AI 7.0 Desktop oynasi ochilmoqda..." -ForegroundColor Cyan

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if (Test-Path $chromePath) {
    Start-Process -FilePath $chromePath -ArgumentList "--app=http://localhost:1420", "--window-size=1280,800"
} elseif (Test-Path $edgePath) {
    Start-Process -FilePath $edgePath -ArgumentList "--app=http://localhost:1420", "--window-size=1280,800"
} else {
    Start-Process "http://localhost:1420"
}

Write-Host "Mikasa AI 7.0 Desktop oynasi ochildi!" -ForegroundColor Green
