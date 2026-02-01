@echo off
REM RepoRadio Startup Script for Windows
REM This script activates the virtual environment and starts the Streamlit app

echo 🎙️ Starting RepoRadio...

REM Check if virtual environment exists
if not exist "venv\" (
    echo ⚠️ Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
    
    echo 📦 Installing dependencies...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ✅ Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️ .env file not found!
    echo 💡 Copy .env.example to .env and configure your API keys
    echo    Example: copy .env.example .env
    echo.
)

REM Run Streamlit
echo 🚀 Launching RepoRadio on http://localhost:8501
echo    Press Ctrl+C to stop
echo.
streamlit run src/app.py
