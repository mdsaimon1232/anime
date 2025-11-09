Anime Downloader & Telegram Uploader Suite
A comprehensive automation suite for downloading anime, processing videos with subtitles, and uploading to Telegram channels automatically.

🚀 Features
Smart Downloading: Auto-detects English dub content from HiAnime

Video Optimization: Converts videos to Telegram-friendly format (480p)

Subtitle Support: Automatic subtitle downloading and embedding

Batch Processing: Handles entire playlists automatically

Telegram Integration: Creates public channels and uploads with progress tracking

Retry Logic: Handles failed downloads and network issues

Speed Optimization: Uses aria2 for faster downloads when available

📁 File Structure
text
anime-downloader/
├── 📄 downen.py            # Main downloader script
├── 📄 comb.py              # Subtitle processor
├── 📄 1.py                 # Telegram channel creator & uploader
├── 📄 requirements.txt     # Python dependencies
├── 📄 setup.sh            # Linux setup script
├── 📄 setup.bat           # Windows setup script
└── 📁 done/               # Processed folders (auto-created)
⚡ Quick Setup
Option 1: Automated Setup (Recommended)
For Linux:

bash
# Make setup script executable and run
chmod +x setup.sh
./setup.sh
For Windows:

Right-click on setup.bat and select "Run as administrator"

Option 2: Manual Setup
If you prefer manual installation:

Install System Dependencies:

Linux:

bash
sudo apt update
sudo apt install ffmpeg aria2 python3 python3-pip
Windows:

cmd
# Using Chocolatey (run as admin)
choco install ffmpeg aria2 python -y
Install Python Packages:

bash
pip install -r requirements.txt
pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
🔧 Telegram API Setup
Go to https://my.telegram.org/

Log in with your phone number

Go to "API Development Tools"

Create a new application

Copy your API_ID and API_HASH

Update these values in 1.py (line 18-19):

python
API_ID = 20509864  # Replace with your actual API ID
API_HASH = '11905c7c10752429a01ceb1b2c42a993'  # Replace with your actual API Hash
🎯 Usage
Step 1: Download Anime
bash
python3 downen.py
Enter HiAnime URL when prompted

Script will automatically download and process videos

Files are organized in series folders

Step 2: Process Subtitles (Automatic)
The comb.py script runs automatically after downloads, but you can run it manually:

bash
python3 comb.py
Step 3: Upload to Telegram
bash
python3 1.py
Automatically creates public Telegram channels

Uploads all videos with progress tracking

Moves processed folders to done/

🔄 Complete Workflow
Run downen.py → Downloads anime from HiAnime

comb.py runs automatically → Converts videos and embeds subtitles

Run 1.py → Creates Telegram channels and uploads content

Automatic cleanup → Moves processed files to done/ folder

⚙️ Configuration
Video Settings
Resolution: 480p (optimized for Telegram)

Format: MP4 with H.264/AAC

Subtitles: English (automatically embedded)

Download Settings
Retry attempts: 10 per video

Concurrent fragments: 5

Rate limit: None (uses maximum available speed)

Telegram Settings
File size limit: 2GB (Telegram maximum)

Upload speed: Adaptive with progress tracking

Channel naming: Automatic with fallback options

🛠️ Troubleshooting
Common Issues
FFmpeg not found:

Run setup script again as administrator

Ensure FFmpeg is in system PATH

Download failures:

Check internet connection

Verify HiAnime URL is accessible

Try running with fewer concurrent downloads

Telegram upload errors:

Verify API_ID and API_HASH are correct in 1.py

Check if Telegram account is active

Ensure files are under 2GB limit

Subtitle issues:

Ensure video and subtitle files have matching episode numbers

Check that FFmpeg is properly installed

Manual Dependency Checks
Check FFmpeg:

bash
ffmpeg -version
Check aria2:

bash
aria2c --version
Check Python packages:

bash
python3 -c "import yt_dlp, requests, telethon; print('All packages installed')"
📝 Notes
Legal: Use responsibly and respect copyright laws

Storage: Ensure sufficient space for downloads and processing

Internet: Stable connection recommended for large uploads

Rate Limiting: Scripts include delays to avoid being blocked

🔄 Updates
To update the system:

bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update yt-dlp with Hianime support  
pip install -U https://github.com/pratikpatel8982/yt-dlp-hianime/archive/master.zip
🤝 Contributing
Feel free to submit issues and enhancement requests!

📄 License
This project is for educational purposes. Please use responsibly and respect content creators' rights.

📋 Script Overview
downen.py
Main downloader script

Handles HiAnime URLs (single videos or playlists)

Automatic English dub detection

Converts videos to 480p MP4 format

Downloads English subtitles

comb.py
Subtitle processing script

Embeds subtitles into video files

Renames files to standardized format

Runs automatically after downloads

1.py
Telegram uploader script

Creates public channels automatically

Uploads videos with progress tracking

Moves processed content to done/ folder

Happy Downloading! 🎉
