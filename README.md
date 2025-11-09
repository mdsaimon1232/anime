# Anime Downloader & Telegram Uploader Suite

A comprehensive automation suite for downloading anime, processing videos with subtitles, and uploading to Telegram channels automatically.

## 🚀 Features

- **Smart Downloading**: Auto-detects English dub content from HiAnime
- **Video Optimization**: Converts videos to Telegram-friendly format (480p)
- **Subtitle Support**: Automatic subtitle downloading and embedding
- **Batch Processing**: Handles entire playlists automatically
- **Telegram Integration**: Creates public channels and uploads with progress tracking
- **Retry Logic**: Handles failed downloads and network issues
- **Speed Optimization**: Uses aria2 for faster downloads when available

## 📁 File Structure

anime-downloader/
├── 📄 downen.py # Main downloader script
├── 📄 comb.py # Subtitle processor
├── 📄 1.py # Telegram channel creator & uploader
├── 📄 requirements.txt # Python dependencies
├── 📄 setup.sh # Linux setup script
├── 📄 setup.bat # Windows setup script
└── 📁 done/ # Processed folders (auto-created)

text

## ⚡ Quick Setup

### Option 1: Automated Setup (Recommended)

**For Linux:**
```bash
chmod +x setup.sh
./setup.sh
For Windows:

Right-click on setup.bat and select "Run as administrator"

Option 2: Manual Setup
Linux:

bash
sudo apt update
sudo apt install ffmpeg aria2 python3 python3-pip
pip install -r requirements.txt
pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
Windows:

cmd
choco install ffmpeg aria2 python -y
pip install -r requirements.txt
pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
🔧 Telegram API Setup
Go to https://my.telegram.org/

Create a new application and get API_ID and API_HASH

Update these values in 1.py

## 🎯 Usage

Step 1: Download Anime
bash
python3 downen.py
Step 2: Process Subtitles (Automatic)
bash
python3 comb.py
Step 3: Upload to Telegram
bash
python3 1.py

## 🔄 Complete Workflow

Run downen.py → Downloads anime from HiAnime

comb.py runs automatically → Embeds subtitles

Run 1.py → Creates Telegram channels and uploads content

## 📝 Notes
Use responsibly and respect copyright laws

Ensure sufficient storage space

Stable internet connection recommended
