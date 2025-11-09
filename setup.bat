@echo off
chcp 65001 >nul
echo ===========================================
echo Anime Downloader & Telegram Uploader Setup
echo ===========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Install Chocolatey if not installed
echo Checking for Chocolatey...
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Chocolatey...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    if %errorLevel% neq 0 (
        echo Failed to install Chocolatey
        pause
        exit /b 1
    )
    echo ✓ Chocolatey installed
) else (
    echo ✓ Chocolatey already installed
)

:: Install FFmpeg
echo Installing FFmpeg...
choco install ffmpeg -y
if %errorLevel% neq 0 (
    echo Failed to install FFmpeg
    pause
    exit /b 1
)
echo ✓ FFmpeg installed

:: Install aria2
echo Installing aria2...
choco install aria2 -y
if %errorLevel% neq 0 (
    echo Failed to install aria2
    pause
    exit /b 1
)
echo ✓ aria2 installed

:: Install Python if not installed
echo Checking for Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Python...
    choco install python -y
    if %errorLevel% neq 0 (
        echo Failed to install Python
        pause
        exit /b 1
    )
    echo ✓ Python installed
) else (
    echo ✓ Python already installed
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorLevel% neq 0 (
    echo Failed to upgrade pip
    pause
    exit /b 1
)
echo ✓ pip upgraded

:: Install Python requirements
echo Installing Python packages...
if exist requirements.txt (
    python -m pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo Failed to install requirements
        pause
        exit /b 1
    )
    echo ✓ Python requirements installed
) else (
    echo requirements.txt not found!
    pause
    exit /b 1
)

:: Install yt-dlp with Hianime support
echo Installing yt-dlp with Hianime support...
python -m pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
if %errorLevel% neq 0 (
    echo Failed to install yt-dlp with Hianime support
    pause
    exit /b 1
)
echo ✓ yt-dlp with Hianime support installed

:: Create directories
echo Creating directories...
if not exist done mkdir done
echo ✓ Directory structure created

echo.
echo ===========================================
echo Setup completed successfully! 🎉
echo ===========================================
echo.
echo Next steps:
echo 1. Get Telegram API credentials from: https://my.telegram.org/
echo 2. Update API_ID and API_HASH in your scripts
echo 3. Run your downloader script: python your_main_script.py
echo.
echo Directory structure:
echo   📁 current-directory/
echo   ├── 📄 your_main_script.py
echo   ├── 📄 comb.py
echo   ├── 📄 1.py
echo   ├── 📄 requirements.txt
echo   ├── 📄 setup.bat
echo   └── 📁 done/ (created after processing)
echo.
pause
