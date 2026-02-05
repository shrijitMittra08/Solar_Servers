@echo off
echo SolarServers - Starting servers...
echo ==================================================

if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then activate it and install requirements:
    echo   .venv\Scripts\activate
    echo   pip install -r Requirements.txt
    pause
    exit /b 1
)

echo Starting backend server on port 8000...
start "SolarServers Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn SolarServers_server:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo Starting frontend server on port 8000...
start "SolarServers Frontend" cmd /k "call .venv\Scripts\activate.bat && cd frontend && python -m http.server 8000"

echo.
echo ==================================================
echo Servers started successfully!
echo Frontend: http://localhost:8000
echo Backend API: http://localhost:8000
echo.
echo Close the command windows to stop the servers
echo ==================================================

pause
