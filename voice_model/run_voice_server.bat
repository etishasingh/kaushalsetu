@echo off
setlocal
title KaushalSetu AI - Standalone Voice Model Backend Server

echo ===============================================================================
echo   KaushalSetu AI -- Voice Model Backend Server
echo ===============================================================================
echo   Starting HTTP API Server on port 8000 with zero external pip dependencies...
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python voice_model_server.py --port 8000
    goto done
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py voice_model_server.py --port 8000
    goto done
)

echo [ERROR] Python was not found in your system PATH!
echo Please install Python 3.8+ to run the backend API server.
echo.
pause

:done
endlocal
