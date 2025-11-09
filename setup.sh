#!/bin/bash

# Anime Downloader & Telegram Uploader - Setup Script
echo "==========================================="
echo "Anime Downloader & Telegram Uploader Setup"
echo "==========================================="

# Function to check if command was successful
check_success() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ Failed: $1"
        exit 1
    fi
}

# Update package list
echo "Updating package list..."
sudo apt update
check_success "Package list updated"

# Install FFmpeg
echo "Installing FFmpeg..."
sudo apt install -y ffmpeg
check_success "FFmpeg installed"

# Install aria2 for faster downloads
echo "Installing aria2..."
sudo apt install -y aria2
check_success "aria2 installed"

# Install Python3 and pip if not already installed
echo "Checking for Python and pip..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    sudo apt install -y python3 python3-pip
    check_success "Python3 installed"
else
    echo "✓ Python3 already installed"
fi

if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    sudo apt install -y python3-pip
    check_success "pip3 installed"
else
    echo "✓ pip3 already installed"
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip
check_success "pip upgraded"

# Install Python requirements
echo "Installing Python packages from requirements.txt..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    check_success "Python requirements installed"
else
    echo "✗ requirements.txt not found!"
    exit 1
fi

# Install yt-dlp with Hianime support
echo "Installing yt-dlp with Hianime support..."
python3 -m pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
check_success "yt-dlp with Hianime support installed"

# Verify installations
echo ""
echo "Verifying installations..."
echo "=========================="

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg: $(ffmpeg -version | head -n1)"
else
    echo "✗ FFmpeg not found"
fi

# Check aria2
if command -v aria2c &> /dev/null; then
    echo "✓ aria2c: $(aria2c --version | head -n1)"
else
    echo "✗ aria2c not found"
fi

# Check Python packages
echo "Checking Python packages..."
python3 -c "
import importlib.util
import sys

packages = [
    ('yt_dlp', 'yt-dlp'),
    ('requests', 'requests'),
    ('telethon', 'telethon')
]

for package, name in packages:
    spec = importlib.util.find_spec(package)
    if spec is not None:
        print(f'✓ {name}: installed')
    else:
        print(f'✗ {name}: not installed')
        sys.exit(1)
"
check_success "All Python packages verified"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p done
check_success "Directory structure created"

# Set execute permissions for Python scripts
echo "Setting execute permissions..."
chmod +x *.py 2>/dev/null || true
check_success "Permissions set"

echo ""
echo "==========================================="
echo "Setup completed successfully! 🎉"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Get Telegram API credentials from: https://my.telegram.org/"
echo "2. Update API_ID and API_HASH in your scripts"
echo "3. Run your downloader script: python3 your_main_script.py"
echo ""
echo "Directory structure:"
echo "  📁 /your/script/directory/"
echo "  ├── 📄 your_main_script.py"
echo "  ├── 📄 comb.py" 
echo "  ├── 📄 1.py"
echo "  ├── 📄 requirements.txt"
echo "  ├── 📄 setup.sh"
echo "  └── 📁 done/ (will be created after processing)"
echo ""
echo "Happy downloading! 🚀"
