@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   LocalScript - MTS True Tech Hack 2026
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

REM Start services
echo [1/4] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)

REM Wait for Ollama
echo.
echo [2/4] Waiting for Ollama to start...
set /a timeout=60
set /a elapsed=0
:wait_ollama
docker exec localscript-ollama curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    if !elapsed! geq !timeout! (
        echo [ERROR] Timeout waiting for Ollama
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    set /a elapsed+=2
    echo | set /p=.
    goto wait_ollama
)
echo.
echo [OK] Ollama is ready

REM Pull model
echo.
echo [3/4] Pulling qwen2.5-coder:7b model...
echo This may take 5-10 minutes on first run
docker exec localscript-ollama ollama pull qwen2.5-coder:7b
if errorlevel 1 (
    echo [ERROR] Failed to pull model
    exit /b 1
)

REM Wait for LocalScript API
echo.
echo [4/4] Waiting for LocalScript API...
set /a timeout=30
set /a elapsed=0
:wait_api
curl -s http://localhost:8000/api/sessions >nul 2>&1
if errorlevel 1 (
    if !elapsed! geq !timeout! (
        echo [ERROR] Timeout waiting for API
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    set /a elapsed+=2
    echo | set /p=.
    goto wait_api
)
echo.
echo [OK] API is ready

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Web UI:  http://localhost:8000
echo API:     http://localhost:8000/docs
echo Ollama:  http://localhost:11434
echo.
echo View logs:    docker-compose logs -f
echo Stop:         docker-compose down
echo Clean all:    docker-compose down -v
echo.
pause
