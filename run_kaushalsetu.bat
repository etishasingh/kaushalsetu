@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo   KAUSHALSETU AI - Integrated Application
echo ================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if defined GEMINI_API_KEY echo Gemini API key detected.
if defined YOUTUBE_API_KEY echo YouTube API key detected.
echo.
echo Starting KaushalSetu at http://127.0.0.1:8000
start "KaushalSetu" http://127.0.0.1:8000
python -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
