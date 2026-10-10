@echo off
echo Building EchecsP2P for Windows (with Stockfish 19)...

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    pause
    exit /b
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Build executable with PyInstaller
echo Building executable with PyInstaller...
pyinstaller --onefile --noconsole --add-data "assets;assets" --add-data "stockfish.exe;." --name EchecsP2P.exe main.py

echo Build complete! Check the 'dist' folder for EchecsP2P.exe.
pause
