@echo off
echo ============================================================
echo   SmartPick — Starting Web Server
echo ============================================================
echo.
echo Activating conda environment...
call conda activate mlproject

echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop.
echo.
python src\app.py
pause
