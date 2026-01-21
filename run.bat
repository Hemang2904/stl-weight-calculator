@echo off
REM STL Weight Calculator - Quick Start Script for Windows

echo ==================================
echo STL Weight Calculator - Setup
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo ✓ Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Install requirements
echo Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo ✓ Dependencies installed
echo.

REM Run the app
echo Starting Streamlit app...
echo.
echo ==================================
echo The app will open in your browser
echo Press Ctrl+C to stop the server
echo ==================================
echo.

streamlit run app.py

pause
