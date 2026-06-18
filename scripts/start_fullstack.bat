@echo off
echo =========================================
echo    CleanCity AI - Starting Full Stack
echo =========================================
echo.

set PROJECT_ROOT=c:\Users\Saurabh kushwaha\Downloads\Smart-Waste-Management-main

echo [1/2] Starting FastAPI backend on http://localhost:8000 ...
start cmd /k "cd /d "%PROJECT_ROOT%" && "%PROJECT_ROOT%\.venv\Scripts\python.exe" -m uvicorn backend_api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Sleep delay using ping
ping 127.0.0.1 -n 4 > nul

echo [2/2] Starting React frontend on http://localhost:3000 ...
start cmd /k "cd /d "%PROJECT_ROOT%\frontend_react" && npm run dev -- --port 3000"

:: Sleep delay using ping
ping 127.0.0.1 -n 4 > nul

echo =========================================
echo   Opening CleanCity AI in Browser...
echo =========================================
echo.

start http://localhost:3000
