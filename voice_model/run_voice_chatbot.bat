@echo off
setlocal
title KaushalSetu AI - Standalone Voice Model Launcher

echo ===============================================================================
echo   KaushalSetu AI -- Standalone Voice Model Launcher
echo ===============================================================================
echo   Starting local Voice Model HTTP server on port 8000...
echo   Opening KaushalSetu Voice Chatbot in your default web browser...
echo.

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python voice_model_server.py --port 8000 --open-browser
    goto done
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py voice_model_server.py --port 8000 --open-browser
    goto done
)

echo [ERROR] Python was not found in your system PATH!
echo.
echo You can still open the Voice Chatbot directly in your browser:
echo Opening "kaushalsetu_voice_chatbot.html" directly...
start "" "%~dp0kaushalsetu_voice_chatbot.html"
echo.
pause

:done
endlocal
