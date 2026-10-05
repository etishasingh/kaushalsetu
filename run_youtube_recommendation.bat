@echo off
chcp 65001 >nul
title KaushalSetu AI — YouTube Career Journey Recommendation Engine
echo ==============================================================================
echo   KaushalSetu AI — YouTube Career Journey Recommendation Engine
echo ==============================================================================
echo.

if "%~1"=="" (
    echo Starting interactive trade exploration...
    python "%~dp0youtube_recommendation.py" --interactive
) else (
    python "%~dp0youtube_recommendation.py" %*
)

echo.
echo ==============================================================================
echo Execution complete.
pause
