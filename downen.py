import yt_dlp
import sys
import os
import subprocess
import shutil
import re

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_for_telegram(input_file, output_file):
    """Convert video to Telegram-compatible format with 480p quality"""
    try:
        cmd = [
            'ffmpeg', '-i', input_file,
            '-c:v', 'libx264',        # H.264 video codec
            '-c:a', 'aac',           # AAC audio codec
            '-b:a', '128k',          # Audio bitrate
            '-movflags', '+faststart', # Enable fast start for streaming
            '-preset', 'fast',        # Encoding speed
            '-crf', '23',            # Quality setting
            '-vf', 'scale=854:480',  # Force 480p resolution
            '-y',                    # Overwrite output file
            output_file
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed: {e}")
        return False

def rename_files_for_telegram(original_file, episode_number, series_name, base_directory):
    """Rename files to simple episode format"""
    try:
        # Create series folder path
        series_folder = os.path.join(base_directory, series_name)
        os.makedirs(series_folder, exist_ok=True)
        
        # Get file extension
        file_ext = os.path.splitext(original_file)[1].lower()
        
        # Determine if it's a video or subtitle file
        if file_ext in ['.mp4', '.mkv', '.avi', '.mov']:
            # Video file
            new_filename = f"Episode {episode_number}{file_ext}"
            new_filepath = os.path.join(series_folder, new_filename)
        elif file_ext in ['.srt', '.vtt', '.ass']:
            # Subtitle file
            new_filename = f"Episode {episode_number}{file_ext}"
            new_filepath = os.path.join(series_folder, new_filename)
        else:
            print(f"Unknown file type: {file_ext}")
            return original_file
        
        # Move and rename the file
        if original_file != new_filepath:
            shutil.move(original_file, new_filepath)
            print(f"✓ Renamed to: {new_filename}")
        
        return new_filepath
        
    except Exception as e:
        print(f"Error renaming file: {e}")
        return original_file

def is_english_dub(title, description=""):
    """Check if the content is English dub"""
    title_lower = title.lower()
    description_lower = description.lower()
    
    # Keywords that indicate English dub
    dub_keywords = ['dub', 'english dub', 'dubbed', 'english']
    # Keywords that indicate sub (we want to avoid these)
    sub_keywords = ['sub', 'subbed', 'subtitled']
    
    # Check for dub indicators
    has_dub = any(keyword in title_lower for keyword in dub_keywords)
    has_dub_desc = any(keyword in description_lower for keyword in dub_keywords)
    
    # Check for sub indicators
    has_sub = any(keyword in title_lower for keyword in sub_keywords)
    has_sub_desc = any(keyword in description_lower for keyword in sub_keywords)
    
    # If it explicitly says dub and doesn't say sub, it's probably English dub
    if (has_dub or has_dub_desc) and not (has_sub or has_sub_desc):
        return True
    
    # If it doesn't specify, assume it's the default (often dub on English sites)
    if not has_sub and not has_sub_desc:
        return True
    
    return False

def get_best_480p_format(formats):
    """Select the best 480p format available"""
    target_height = 480
    best_format = None
    
    for fmt in formats:
        if fmt.get('height') == target_height:
            # Prefer formats with both video and audio
            if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none':
                if best_format is None or fmt.get('filesize', 0) > best_format.get('filesize', 0):
                    best_format = fmt
    
    # If no combined format found, look for video-only 480p
    if best_format is None:
        for fmt in formats:
            if fmt.get('height') == target_height and fmt.get('vcodec') != 'none':
                if best_format is None or fmt.get('filesize', 0) > best_format.get('filesize', 0):
                    best_format = fmt
    
    return best_format

def download_video_with_subtitles(url, ydl_opts, convert_for_telegram_flag=True, base_directory="F:/anime/english/new"):
    """Download a single video with subtitles, ensuring English dub and 480p quality"""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to see what we're dealing with
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown title')
            description = info.get('description', '')
            
            # Check if this is English dub
            if not is_english_dub(title, description):
                print(f"⚠ Warning: This might not be English dub content")
                print(f"Title: {title}")
                user_choice = input("Do you want to continue anyway? (y/n): ")
                if user_choice.lower() != 'y':
                    print("Skipping download...")
                    return None
            
            series_name = info.get('series', 'Unknown Series')
            episode_number = info.get('episode_number', 1)
            
            print(f"Downloading: {title}")
            print(f"Series: {series_name}, Episode: {episode_number}")
            
            # Check available formats and select 480p
            available_formats = info.get('formats', [])
            best_480p = get_best_480p_format(available_formats)
            
            if best_480p:
                format_id = best_480p['format_id']
                print(f"Selected 480p format: {format_id} ({best_480p.get('width')}x{best_480p.get('height')})")
                # Update format selection
                ydl_opts['format'] = format_id
            else:
                print("⚠ No 480p format found. Falling back to best available format up to 480p")
                ydl_opts['format'] = 'best[height<=480]'
            
            # Check for available subtitles
            available_subs = info.get('subtitles', {}) or info.get('automatic_captions', {})
            if available_subs:
                print(f"Available subtitle languages: {list(available_subs.keys())}")
            else:
                print("No subtitles available for this video")
            
            # Download the video with subtitles
            ydl.download([url])
            
            # Get the actual downloaded filename
            filename = ydl.prepare_filename(info)
            
            print(f"✓ Completed: {title}")
            
            final_files = []
            
            # Convert for Telegram if requested and ffmpeg is available
            if convert_for_telegram_flag and check_ffmpeg():
                print("Converting for Telegram compatibility (480p)...")
                base_name = os.path.splitext(filename)[0]
                output_file = f"{base_name}_telegram.mp4"
                
                if convert_for_telegram(filename, output_file):
                    print(f"✓ Telegram-compatible 480p version created")
                    # Remove original file to save space
                    if os.path.exists(filename):
                        os.remove(filename)
                    
                    # Rename the converted file
                    renamed_file = rename_files_for_telegram(
                        output_file, episode_number, series_name, base_directory
                    )
                    final_files.append(renamed_file)
                else:
                    print("✗ Failed to create Telegram-compatible version")
                    # Rename the original file
                    renamed_file = rename_files_for_telegram(
                        filename, episode_number, series_name, base_directory
                    )
                    final_files.append(renamed_file)
            else:
                if convert_for_telegram_flag and not check_ffmpeg():
                    print("⚠ FFmpeg not found. Cannot convert for Telegram.")
                
                # Rename the original file
                renamed_file = rename_files_for_telegram(
                    filename, episode_number, series_name, base_directory
                )
                final_files.append(renamed_file)
            
            # Also rename subtitle files if they exist
            subtitle_patterns = ['.en.srt', '.srt', '.vtt', '.ass']
            for pattern in subtitle_patterns:
                subtitle_file = os.path.splitext(filename)[0] + pattern
                if os.path.exists(subtitle_file):
                    renamed_subtitle = rename_files_for_telegram(
                        subtitle_file, episode_number, series_name, base_directory
                    )
                    final_files.append(renamed_subtitle)
            
            return final_files
            
    except Exception as e:
        print(f"✗ Error downloading {url}: {e}")
        return None

def run_comb_script():
    """Run the comb.py script after all downloads are complete"""
    try:
        print("\n" + "="*50)
        print("All downloads completed. Running comb.py...")
        print("="*50)
        
        # Check if comb.py exists in the current directory
        if os.path.exists("comb.py"):
            result = subprocess.run([sys.executable, "comb.py"], capture_output=True, text=True)
            print("comb.py output:")
            print(result.stdout)
            if result.stderr:
                print("comb.py errors:")
                print(result.stderr)
            print("✓ comb.py execution completed")
        else:
            print("⚠ comb.py not found in current directory")
            
    except Exception as e:
        print(f"✗ Error running comb.py: {e}")

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Please enter the HiAnime URL to download: ")

    # Base directory for downloads
    base_directory = "F:/anime/english/new"
    
    # Create base directory if it doesn't exist
    os.makedirs(base_directory, exist_ok=True)

    # Check if user wants Telegram conversion
    convert_for_tg = True
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['false', '0', 'no', 'n']:
            convert_for_tg = False

    ydl_opts = {
        'outtmpl': os.path.join(base_directory, '%(series)s', '%(series)s - %(episode_number)s - %(episode)s.%(ext)s'),
        'verbose': True,
        # Force 480p quality
        'format': 'best[height<=480]',  # Start with 480p or lower
        'concurrent_fragments': 50,
        'fragment_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        },
        'nocheckcertificate': True,
        # Subtitle options
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'srt',  # Use SRT format for better compatibility
        'embed-subs': True,
        # Post-processing options for better Telegram compatibility
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Convert to MP4 container
            }
        ],
    }

    try:
        # First, check if it's a playlist or single video
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if 'entries' in info:
            # It's a playlist
            print(f"Found playlist with {len(info['entries'])} videos")
            all_downloaded_files = []
            
            for i, entry in enumerate(info['entries'], 1):
                if entry:  # Some entries might be None
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if video_url:
                        print(f"\n--- Processing video {i}/{len(info['entries'])} ---")
                        result_files = download_video_with_subtitles(
                            video_url, ydl_opts, convert_for_tg, base_directory
                        )
                        
                        if result_files:
                            all_downloaded_files.extend(result_files)
                            print(f"✓ Successfully processed video {i}")
                        else:
                            print(f"✗ Failed to process video {i}")
                            continue
                            
                        # Add delay between downloads to avoid being blocked
                        if i < len(info['entries']):
                            print("Waiting 3 seconds before next download...")
                            import time
                            time.sleep(3)
                    else:
                        print(f"Could not get URL for video {i}")
                else:
                    print(f"Empty entry at position {i}")
                    
            print(f"\n🎉 Playlist download completed! Processed {len(all_downloaded_files)} files.")
            print("Files ready for Telegram:")
            for file in all_downloaded_files:
                print(f"  - {file}")
            
        else:
            # It's a single video
            print("Downloading single video...")
            result_files = download_video_with_subtitles(url, ydl_opts, convert_for_tg, base_directory)
            if result_files:
                print(f"🎉 Single video download completed!")
                print("Files ready for Telegram:")
                for file in result_files:
                    print(f"  - {file}")
            else:
                print("❌ Failed to download video")
        
        # Run comb.py after all downloads are complete
        run_comb_script()
                
    except Exception as e:
        print(f"An error occurred: {e}")
        # Even if there was an error, try to run comb.py if we downloaded some files
        run_comb_script()

if __name__ == "__main__":
    main()