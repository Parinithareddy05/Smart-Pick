@echo off
echo ============================================================
echo   SmartPick — Windows Setup
echo ============================================================
echo.

REM ── Step 1: Create conda environment ──────────────────────────
echo [1/4] Creating conda environment "mlproject"...
call conda create -n mlproject python=3.10 -y
if %errorlevel% neq 0 (
    echo ERROR: conda not found. Install Miniconda from:
    echo   https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

REM ── Step 2: Install Python packages ───────────────────────────
echo.
echo [2/4] Installing Python packages...
call conda activate mlproject && pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

REM ── Step 3: Install Playwright browsers ───────────────────────
echo.
echo [3/4] Installing Playwright browsers (Chromium + Firefox)...
call conda activate mlproject && python -m playwright install chromium firefox
if %errorlevel% neq 0 (
    echo ERROR: Playwright browser install failed.
    pause
    exit /b 1
)

REM ── Step 4: Create data folder ────────────────────────────────
echo.
echo [4/4] Creating data folder...
if not exist "data" mkdir data
if not exist "results\charts" mkdir results\charts

echo.
echo ============================================================
echo   Setup complete!
echo   Now run:  run_windows.bat
echo ============================================================
pause
