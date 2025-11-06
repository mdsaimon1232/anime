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

# Configuration
BASE_PATH = r"F:\anime\english\new"
DONE_PATH = r"F:\anime\english\done"
API_ID = 1234567  # Replace with your actual API ID
API_HASH = 'your_api_hash_here'  # Replace with your actual API Hash

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
    Get all folder names in the base path
    """
    anime_folders = []
    
    try:
        if not os.path.exists(BASE_PATH):
            print(f"Error: Path {BASE_PATH} does not exist!")
            return anime_folders
            
        for item in os.listdir(BASE_PATH):
            item_path = os.path.join(BASE_PATH, item)
            if os.path.isdir(item_path):
                anime_folders.append(item)
                
    except Exception as e:
        print(f"Error accessing path {BASE_PATH}: {e}")
    
    return anime_folders

def get_video_files(folder_path):
    """
    Get all video files from a folder
    """
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
    video_files = []
    
    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in video_extensions):
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
    Upload all video files from folder to channel
    """
    video_files = get_video_files(folder_path)
    
    if not video_files:
        print("❌ No video files found in the folder!")
        return 0
    
    print(f"🎬 Found {len(video_files)} video files to upload")
    
    uploaded_count = 0
    for video_file in video_files:
        try:
            # Get caption from filename (without extension)
            caption = os.path.splitext(os.path.basename(video_file))[0]
            
            print(f"⬆️ Uploading: {caption}")
            
            # Upload the video file
            await client.send_file(
                entity=channel.id,
                file=video_file,
                caption=caption,
                supports_streaming=True
            )
            
            uploaded_count += 1
            print(f"✅ Uploaded: {caption}")
            
            # Add a small delay between uploads to avoid rate limiting
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error uploading {video_file}: {e}")
    
    print(f"🎉 Upload completed! {uploaded_count}/{len(video_files)} videos uploaded successfully")
    return uploaded_count

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
    
    # Step 4: Upload all videos to the channel
    uploaded_count = await upload_videos_to_channel(client, channel, folder_path)
    
    # Step 5: Move folder to done directory if at least one video was uploaded
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
    anime_folders = get_anime_folders()
    
    if not anime_folders:
        print("❌ No folders found in the specified path!")
        return
    
    print(f"📊 Found {len(anime_folders)} anime folders")
    
    # Initialize Telegram client
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
            
            # Add delay between processing folders to avoid rate limiting
            if i < len(anime_folders):
                print("⏳ Waiting before processing next folder...")
                await asyncio.sleep(10)
    
    print(f"\n🎊 All done! Successfully processed {successful_processing}/{len(anime_folders)} anime folders")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())