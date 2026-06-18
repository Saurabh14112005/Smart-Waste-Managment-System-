# Starts FastAPI :8000 which serves both API and Dashboard. Run from repo after venv + pip install.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Create venv: python -m venv .venv ; .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$apiCmd = "Set-Location '$ProjectRoot'; & '$ProjectRoot\.venv\Scripts\Activate.ps1'; python -m uvicorn backend_api.main:app --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd

Start-Sleep -Seconds 3

# Open dashboard in browser
Start-Process "http://localhost:8000"

Write-Host "API docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Green
