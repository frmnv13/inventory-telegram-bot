@echo off
echo Starting Telegram Inventory Bot...

REM Navigate to the project directory
cd /d "%~dp0"

REM Check if venv exists. If not, create it and install dependencies.
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo Running bot.py from the virtual environment...
REM Run the Python script
python bot.py

REM Pause the script to see any error messages before the window closes
pause
