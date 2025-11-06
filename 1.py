import os
import asyncio
import requests
import time
import shutil
from pathlib import Path
from telethon import TelegramClient
from telethon import functions, types
from telethon.tl.types import InputChatUploadedPhoto
import random

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration - now using the script directory
BASE_PATH = SCRIPT_DIR  # Look for folders where script is located
DONE_PATH = os.path.join(SCRIPT_DIR, "done")  # Create 'done' folder in script directory
API_ID = 20509864  # Replace with your actual API ID
API_HASH = '11905c7c10752429a01ceb1b2c42a993'  # Replace with your actual API Hash

def generate_username(channel_name, suffix=None):
    """Generate username from channel name with multiple fallback options"""
    if suffix is None:
        suffix = str(random.randint(100, 999))
    
    # Clean the base name
    base_username = channel_name.replace(' ', '_').lower()
    clean_username = ''.join(char for char in base_username if char.isalnum() or char == '_')
    
    # Remove multiple consecutive underscores
    while '__' in clean_username:
        clean_username = clean_username.replace('__', '_')
    
    # Remove leading/trailing underscores
    clean_username = clean_username.strip('_')
    
    # If username is too short, pad it
    if len(clean_username) < 3:
        clean_username = f"channel_{clean_username}"
    
    # Truncate if too long (Telegram limit is 32 chars, we reserve 4 for suffix)
    if len(clean_username) > 28:
        clean_username = clean_username[:28]
    
    # Generate the final username
    final_username = f"{clean_username}_{suffix}"
    
    return final_username

def search_anime_poster(anime_name):
    """
    Search for anime poster using AniList GraphQL API
    Returns image URL if found, None otherwise
    """
    try:
        # GraphQL query for AniList API
        query = '''
        query ($search: String) {
            Media (search: $search, type: ANIME) {
                title {
                    romaji
                    english
                }
                coverImage {
                    large
                    extraLarge
                }
            }
        }
        '''
        
        variables = {'search': anime_name}
        
        response = requests.post(
            'https://graphql.anilist.co',
            json={'query': query, 'variables': variables},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if (data.get('data') and 
            data['data'].get('Media') and 
            data['data']['Media'].get('coverImage')):
            
            # Prefer extraLarge, fall back to large
            image_url = (data['data']['Media']['coverImage'].get('extraLarge') or 
                        data['data']['Media']['coverImage'].get('large'))
            return image_url
            
    except Exception as e:
        print(f"Error searching for {anime_name}: {e}")
    
    return None

def download_image(img_url, folder_path, anime_name):
    """
    Download image from URL and save to folder
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(img_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Determine file extension from URL or Content-Type
        if '.' in img_url:
            extension = img_url.split('.')[-1].lower()
            if extension in ['jpg', 'jpeg', 'png', 'webp']:
                file_extension = extension
            else:
                file_extension = 'jpg'
        else:
            # Default to jpg if cannot determine
            file_extension = 'jpg'
        
        # Clean anime name for filename
        clean_name = "".join(c for c in anime_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"poster.{file_extension}"
        filepath = os.path.join(folder_path, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded poster for: {anime_name}")
        return filepath
        
    except Exception as e:
        print(f"✗ Failed to download image for {anime_name}: {e}")
        return None

def get_anime_folders():
    """
    Get all folder names in the base path (script directory)
    """
    anime_folders = []
    
    try:
        if not os.path.exists(BASE_PATH):
            print(f"Error: Path {BASE_PATH} does not exist!")
            return anime_folders
            
        for item in os.listdir(BASE_PATH):
            item_path = os.path.join(BASE_PATH, item)
            if os.path.isdir(item_path):
                # Skip the 'done' folder and system folders
                if item.lower() != 'done' and not item.startswith('.'):
                    anime_folders.append(item)
                
    except Exception as e:
        print(f"Error accessing path {BASE_PATH}: {e}")
    
    return anime_folders

def get_video_files(folder_path):
    """
    Get all video files from a folder with size checking
    """
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
    video_files = []
    
    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in video_extensions):
                file_size = os.path.getsize(file_path)
                file_size_gb = file_size / (1024*1024*1024)
                
                # Check if file is too large for Telegram
                if file_size_gb > 1.9:  # Telegram limit is ~2GB
                    print(f"⚠️ File too large for Telegram: {file} ({file_size_gb:.2f} GB)")
                    continue
                    
                video_files.append(file_path)
    except Exception as e:
        print(f"Error reading video files from {folder_path}: {e}")
    
    # Sort files naturally (episode 1, episode 2, etc.)
    video_files.sort()
    return video_files

async def create_public_telegram_channel(client, channel_name):
    """
    Create a public Telegram channel with the given name
    Returns channel object and username if successful
    """
    if not channel_name:
        print("❌ Channel name cannot be empty!")
        return None, None
    
    # Generate username automatically
    channel_username = generate_username(channel_name)
    
    print(f"📢 Channel Name: {channel_name}")
    print(f"🔗 Generated Username: {channel_username}")
    
    try:
        # Step 1: Create the channel (initially private)
        print("Creating channel...")
        result = await client(functions.channels.CreateChannelRequest(
            title=channel_name,
            about=f"This is {channel_name} anime channel",
            megagroup=False,  # False for broadcast channel
        ))
        
        channel = result.chats[0]
        print(f"✅ Channel created successfully! (Currently private)")
        print(f"📢 Channel Title: {channel.title}")
        print(f"🆔 Channel ID: {channel.id}")
        
        # Try to set username
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                await client(functions.channels.UpdateUsernameRequest(
                    channel=channel.id,
                    username=channel_username
                ))
                
                print(f"🌐 Channel is now public!")
                print(f"🔗 Channel Link: https://t.me/{channel_username}")
                return channel, channel_username
                
            except Exception as e:
                if "USERNAME_OCCUPIED" in str(e) and attempt < max_attempts - 1:
                    print(f"❌ Username {channel_username} is taken, trying alternative...")
                    channel_username = generate_username(channel_name, str(random.randint(100, 999)))
                    print(f"🔗 New generated Username: {channel_username}")
                    continue
                else:
                    print(f"❌ Error setting username: {e}")
                    print("The channel was created but remains private.")
                    return channel, None
                    
    except Exception as e:
        print(f"❌ Error creating channel {channel_name}: {e}")
        return None, None

async def upload_channel_photo(client, channel, image_path):
    """
    Upload and set channel photo
    """
    try:
        print(f"🖼️ Uploading channel photo...")
        await client(functions.channels.EditPhotoRequest(
            channel=channel.id,
            photo=await client.upload_file(image_path)
        ))
        print(f"✅ Channel photo set successfully!")
        return True
    except Exception as e:
        print(f"❌ Error setting channel photo: {e}")
        return False

async def upload_videos_to_channel(client, channel, folder_path):
    """
    Upload all video files from folder to channel with retry logic and progress monitoring
    """
    video_files = get_video_files(folder_path)
    
    if not video_files:
        print("❌ No video files found in the folder!")
        return 0
    
    print(f"🎬 Found {len(video_files)} video files to upload")
    
    uploaded_count = 0
    for i, video_file in enumerate(video_files, 1):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get caption from filename (without extension)
                caption = os.path.splitext(os.path.basename(video_file))[0]
                file_size_gb = os.path.getsize(video_file) / (1024*1024*1024)
                
                print(f"⬆️ Uploading ({i}/{len(video_files)}): {caption}")
                print(f"📊 File size: {file_size_gb:.2f} GB")
                
                # Progress tracking variables
                start_time = time.time()
                last_progress = 0
                last_time = start_time
                uploaded_bytes = 0
                
                def progress_callback(current, total):
                    nonlocal last_progress, last_time, uploaded_bytes
                    current_time = time.time()
                    uploaded_bytes = current
                    
                    percent = (current / total) * 100 if total > 0 else 0
                    
                    # Calculate speed every 5 seconds or when significant progress is made
                    time_diff = current_time - last_time
                    if time_diff >= 5 or current == total:  # Update every 5 seconds or at completion
                        progress_diff = current - last_progress
                        if time_diff > 0:
                            speed_mbps = (progress_diff * 8) / (time_diff * 1000000)  # Convert to Mbps
                            speed_mbps_display = min(speed_mbps, 1000)  # Cap display at 1000 Mbps
                            
                            time_elapsed = current_time - start_time
                            if current > 0 and current < total:
                                # Estimate remaining time
                                upload_speed = current / time_elapsed  # bytes per second
                                remaining_bytes = total - current
                                if upload_speed > 0:
                                    remaining_seconds = remaining_bytes / upload_speed
                                    remaining_time = f" | ETA: {remaining_seconds:.0f}s"
                                else:
                                    remaining_time = " | ETA: Calculating..."
                            else:
                                remaining_time = ""
                            
                            print(f"📤 Progress: {percent:.1f}% | Speed: {speed_mbps_display:.2f} Mbps{remaining_time}", end='\r')
                        
                        last_progress = current
                        last_time = current_time
                
                # Upload the video file with progress callback
                await client.send_file(
                    entity=channel.id,
                    file=video_file,
                    caption=caption,
                    supports_streaming=True,
                    progress_callback=progress_callback
                )
                
                upload_time = time.time() - start_time
                speed_gb_h = (file_size_gb / (upload_time / 3600)) if upload_time > 0 else 0
                
                uploaded_count += 1
                print(f"\n✅ Uploaded: {caption} in {upload_time:.1f}s ({speed_gb_h:.2f} GB/h)")
                
                break  # Success, break out of retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30  # 30, 60, 90 seconds
                    print(f"⚠️ Upload failed, retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Failed to upload {video_file} after {max_retries} attempts: {e}")
        
        # Increased delay between uploads
        if i < len(video_files):
            delay = random.uniform(10, 30)  # 10-30 second delay
            print(f"⏳ Waiting {delay:.1f} seconds before next upload...")
            await asyncio.sleep(delay)
    
    print(f"🎉 Upload completed! {uploaded_count}/{len(video_files)} videos uploaded successfully")
    return uploaded_count

async def test_upload_speed(client, channel):
    """Test upload speed with a small file"""
    test_file = "test_upload.bin"
    
    try:
        # Create a 5MB test file (smaller for faster testing)
        print("🧪 Testing upload speed to Telegram servers...")
        with open(test_file, 'wb') as f:
            f.write(os.urandom(5 * 1024 * 1024))  # 5MB
        
        start_time = time.time()
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"🧪 Speed Test Progress: {percent:.1f}%", end='\r')
        
        await client.send_file(
            entity=channel.id,
            file=test_file,
            caption="Speed test file - please ignore",
            progress_callback=progress_callback
        )
        
        upload_time = time.time() - start_time
        speed_mbps = (5 * 8) / upload_time  # Convert to Mbps (5MB * 8 bits/byte / time)
        print(f"\n📊 Actual upload speed to Telegram: {speed_mbps:.2f} Mbps")
        return speed_mbps
        
    except Exception as e:
        print(f"❌ Speed test failed: {e}")
        return None
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def move_folder_to_done(folder_name):
    """
    Move the processed folder to the done directory
    """
    try:
        # Create done directory if it doesn't exist
        if not os.path.exists(DONE_PATH):
            os.makedirs(DONE_PATH)
            print(f"📁 Created directory: {DONE_PATH}")
        
        source_path = os.path.join(BASE_PATH, folder_name)
        destination_path = os.path.join(DONE_PATH, folder_name)
        
        # Check if destination already exists
        counter = 1
        original_destination = destination_path
        while os.path.exists(destination_path):
            destination_path = f"{original_destination}_{counter}"
            counter += 1
        
        # Move the folder
        shutil.move(source_path, destination_path)
        print(f"📦 Moved folder to: {destination_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error moving folder {folder_name} to done directory: {e}")
        return False

async def process_anime_folder(client, folder_name):
    """
    Process a single anime folder: create channel, upload poster, upload videos
    """
    print(f"\n{'='*60}")
    print(f"🚀 Processing: {folder_name}")
    print(f"{'='*60}")
    
    folder_path = os.path.join(BASE_PATH, folder_name)
    
    # Step 1: Search and download poster
    print("🔍 Searching for anime poster...")
    poster_url = search_anime_poster(folder_name)
    
    poster_path = None
    if poster_url:
        poster_path = download_image(poster_url, folder_path, folder_name)
        if not poster_path:
            print("⚠️ Could not download poster, continuing without it...")
    else:
        print("⚠️ No poster found, continuing without it...")
    
    # Step 2: Create Telegram channel
    channel, username = await create_public_telegram_channel(client, folder_name)
    
    if not channel:
        print(f"❌ Failed to create channel for {folder_name}, skipping...")
        return False
    
    # Step 3: Upload channel photo if poster was downloaded
    if poster_path and os.path.exists(poster_path):
        await upload_channel_photo(client, channel, poster_path)
    
    # Step 4: Run speed test (optional)
    run_speed_test = True  # Set to False to skip speed test
    if run_speed_test:
        await test_upload_speed(client, channel)
        await asyncio.sleep(5)  # Brief pause after speed test
    
    # Step 5: Upload all videos to the channel
    uploaded_count = await upload_videos_to_channel(client, channel, folder_path)
    
    # Step 6: Move folder to done directory if at least one video was uploaded
    if uploaded_count > 0:
        print(f"📦 Moving folder to done directory...")
        if move_folder_to_done(folder_name):
            print(f"✅ Successfully processed and moved: {folder_name}")
            return True
        else:
            print(f"⚠️ Processing completed but failed to move folder: {folder_name}")
            return False
    else:
        print(f"⚠️ No videos were uploaded for {folder_name}, folder not moved")
        return False

async def main():
    """
    Main function to process all anime folders
    """
    # Get all anime folders
    print("📁 Scanning for anime folders...")
    print(f"📂 Looking in: {BASE_PATH}")
    anime_folders = get_anime_folders()
    
    if not anime_folders:
        print("❌ No folders found in the script directory!")
        print("💡 Place your anime folders in the same directory as this script.")
        return
    
    print(f"📊 Found {len(anime_folders)} anime folders")
    
    # Initialize Telegram client (keeping your original session name)
    async with TelegramClient('session_name', API_ID, API_HASH) as client:
        print("🔗 Connecting to Telegram...")
        await client.start()
        print("✅ Successfully logged in!")
        
        # Process each folder
        successful_processing = 0
        for i, folder_name in enumerate(anime_folders, 1):
            print(f"\n📦 Processing folder {i}/{len(anime_folders)}")
            if await process_anime_folder(client, folder_name):
                successful_processing += 1
            
            # Increased delay between processing folders
            if i < len(anime_folders):
                delay = random.uniform(60, 120)  # 1-2 minute delay
                print(f"⏳ Waiting {delay:.1f} seconds before next folder...")
                await asyncio.sleep(delay)
    
    print(f"\n🎊 All done! Successfully processed {successful_processing}/{len(anime_folders)} anime folders")
    print(f"📁 Processed folders moved to: {DONE_PATH}")

if __name__ == "__main__":
    # Display script information
    print("🤖 Anime Telegram Channel Creator")
    print("=" * 50)
    print(f"📂 Script Location: {SCRIPT_DIR}")
    print(f"📁 Source Folder: {BASE_PATH}")
    print(f"📦 Done Folder: {DONE_PATH}")
    print("=" * 50)
    
    # Run the main function
    asyncio.run(main())
