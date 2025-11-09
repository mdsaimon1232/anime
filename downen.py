import yt_dlp
import sys
import os
import subprocess
import shutil
import re
import requests
import time
import threading

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_aria2():
    """Check if aria2c is available for faster downloads"""
    try:
        subprocess.run(['aria2c', '--version'], capture_output=True, check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def speed_test():
    """Test download speed to identify bottlenecks"""
    test_url = "http://speedtest.ftp.otenet.gr/files/test1Mb.db"
    
    try:
        start_time = time.time()
        response = requests.get(test_url, stream=True)
        total_size = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            total_size += len(chunk)
            elapsed = time.time() - start_time
            if elapsed > 0:
                speed = total_size / elapsed / 1024  # KB/s
                print(f"\rSpeed Test: {speed:.2f} KB/s", end='')
            
            if elapsed > 10:  # Test for 10 seconds max
                break
        
        print(f"\nFinal Speed: {speed:.2f} KB/s")
        return speed
    except Exception as e:
        print(f"Speed test failed: {e}")
        return 0

def convert_for_telegram(input_file, output_file, timeout=300):
    """Convert video to Telegram-compatible format with 480p quality and timeout"""
    try:
        print(f"Starting FFmpeg conversion with {timeout} second timeout...")
        
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
        
        # Run with timeout and capture output
        process = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        print("✓ FFmpeg conversion completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"✗ FFmpeg conversion timed out after {timeout} seconds")
        # Try to kill any lingering FFmpeg processes
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'ffmpeg.exe'], 
                             capture_output=True, timeout=10)
            else:  # Linux/Mac
                subprocess.run(['pkill', '-f', 'ffmpeg'], 
                             capture_output=True, timeout=10)
        except:
            pass
        return False
    except subprocess.CalledProcessError as e:
        print(f"✗ FFmpeg conversion failed: {e}")
        if e.stderr:
            print(f"FFmpeg error: {e.stderr[:500]}...")  # Print first 500 chars
        return False
    except Exception as e:
        print(f"✗ Unexpected error during conversion: {e}")
        return False

def rename_files_for_telegram(original_file, episode_number, series_name, base_directory):
    """Rename files to simple episode format"""
    try:
        # Create series folder path - now in the same directory as script
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

def get_best_dub_format_by_preference(formats, prefer_dub=True):
    """
    Select DUBBED format with resolution preference:
    360p -> 480p -> 720p -> 1080p
    """
    # Define resolution preference order (lowest to highest)
    resolution_preference = [360, 480, 720, 1080]
    
    dub_formats = []
    sub_formats = []

    # Classify formats as SUB or DUB based on format_id
    for fmt in formats:
        format_id = fmt.get('format_id', '').lower()
        if 'dub' in format_id:
            dub_formats.append(fmt)
        elif 'sub' in format_id:
            sub_formats.append(fmt)

    # If we prefer dub and have dubbed formats, use those
    if prefer_dub and dub_formats:
        candidate_formats = dub_formats
        print("  Targeting DUBBED formats")
    else:
        candidate_formats = formats
        print("  Warning: No clear DUB formats found, falling back to all formats")

    # Try each resolution in preference order
    for target_res in resolution_preference:
        for fmt in candidate_formats:
            if fmt.get('height') == target_res:
                print(f"  Found preferred DUB format: {fmt.get('format_id')} ({target_res}p)")
                return fmt
    
    # If no preferred resolution found, return the first available dubbed format
    if candidate_formats:
        fallback_format = candidate_formats[0]
        print(f"  No preferred resolution found, using fallback: {fallback_format.get('format_id')} ({fallback_format.get('height')}p)")
        return fallback_format
    
    print("  No suitable DUB format found!")
    return None

def is_english_dub(info_dict):
    """
    Improved detection using format information from the extractor.
    Returns True if DUB formats are explicitly available.
    """
    # Check available formats for DUB indicators
    formats = info_dict.get('formats', [])
    available_subs = info_dict.get('subtitles', {})
    available_auto_subs = info_dict.get('automatic_captions', {})
    
    dub_format_count = 0
    for fmt in formats:
        format_id = fmt.get('format_id', '').lower()
        format_note = fmt.get('format_note', '').lower()
        
        # Look for unambiguous DUB indicators in format metadata
        if any(keyword in format_id for keyword in ['dub', 'english']) or \
           any(keyword in format_note for keyword in ['dub', 'dubbed', 'english']):
            dub_format_count += 1
            
    print(f"  Found {dub_format_count} format(s) with DUB indicators")
    
    # If we found explicit DUB formats, trust that
    if dub_format_count > 0:
        return True
        
    # Additional fallback: check title and description
    title = info_dict.get('title', '').lower()
    description = info_dict.get('description', '').lower()
    
    dub_keywords = ['dub', 'dubbed', 'english dub']
    sub_keywords = ['sub', 'subbed', 'subtitled']
    
    has_dub = any(keyword in title for keyword in dub_keywords)
    has_dub_desc = any(keyword in description for keyword in dub_keywords)
    has_sub = any(keyword in title for keyword in sub_keywords)
    
    return (has_dub or has_dub_desc) and not has_sub

def download_video_with_subtitles_with_retry(url, ydl_opts, convert_for_telegram_flag=True, base_directory=None, max_retries=10):
    """Download a single video with retry logic for failed attempts"""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n🔄 Attempt {attempt}/{max_retries} for URL: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to see what we're dealing with
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Unknown title')
                description = info.get('description', '')
                formats = info.get('formats', [])
                
                # IMPROVED: Detailed format analysis
                print("=== FORMAT ANALYSIS ===")
                for i, fmt in enumerate(info.get('formats', [])):
                    print(f"Format {i}: ID={fmt.get('format_id')}, "
                          f"Note={fmt.get('format_note')}, "
                          f"Height={fmt.get('height')}, "
                          f"Codec={fmt.get('vcodec')}/{fmt.get('acodec')}")
                print("=======================")
                
                # IMPROVED: Use the new DUB detection
                if not is_english_dub(info):
                    print(f"⚠ Warning: This might not be English dub content")
                    print(f"Title: {title}")
                    
                    if attempt == 1:  # Only ask on first attempt
                        user_choice = input("Do you want to continue anyway? (y/n): ")
                        if user_choice.lower() != 'y':
                            print("Skipping download...")
                            return None
                else:
                    print("✓ English dub content detected")
                
                series_name = info.get('series', 'Unknown Series')
                episode_number = info.get('episode_number', 1)
                
                print(f"Downloading: {title}")
                print(f"Series: {series_name}, Episode: {episode_number}")
                
                # IMPROVED: Use the new resolution-preference format selector
                available_formats = info.get('formats', [])
                print("Available format IDs:", [f.get('format_id') for f in available_formats])

                # Use the new resolution-preference format selector
                best_format = get_best_dub_format_by_preference(available_formats, prefer_dub=True)

                if best_format:
                    format_id = best_format['format_id']
                    height = best_format.get('height', 'unknown')
                    # Check if the selected format is actually a DUB format
                    is_dub_format = 'dub' in format_id.lower()
                    print(f"Selected format: {format_id} ({height}p, DUB: {is_dub_format})")
                    ydl_opts['format'] = format_id
                else:
                    print("No suitable dubbed format found. Using general format selection with resolution preference.")
                    # Fallback that respects resolution preference
                    ydl_opts['format'] = 'best[height<=360]/best[height<=480]/best[height<=720]/best[height<=1080]/best'
                
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
                
                # Convert for Telegram if requested and ffmpeg is available AND file is not already MP4
                if convert_for_telegram_flag and check_ffmpeg() and not filename.lower().endswith('.mp4'):
                    print("Converting for Telegram compatibility (480p)...")
                    base_name = os.path.splitext(filename)[0]
                    output_file = f"{base_name}_telegram.mp4"
                    
                    if convert_for_telegram(filename, output_file, timeout=300):
                        print(f"✓ Telegram-compatible 480p version created")
                        # Remove original file to save space
                        if os.path.exists(filename):
                            os.remove(filename)
                            print("✓ Original file removed")
                        
                        # Rename the converted file
                        renamed_file = rename_files_for_telegram(
                            output_file, episode_number, series_name, base_directory
                        )
                        final_files.append(renamed_file)
                    else:
                        print("✗ Failed to create Telegram-compatible version")
                        # Keep original file and rename it
                        renamed_file = rename_files_for_telegram(
                            filename, episode_number, series_name, base_directory
                        )
                        final_files.append(renamed_file)
                else:
                    # Skip conversion if file is already MP4 or FFmpeg not available
                    if convert_for_telegram_flag and not check_ffmpeg():
                        print("⚠ FFmpeg not found. Cannot convert for Telegram.")
                    elif convert_for_telegram_flag and filename.lower().endswith('.mp4'):
                        print("✓ File is already in MP4 format, skipping conversion")
                    
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
            print(f"✗ Error downloading {url} (Attempt {attempt}/{max_retries}): {e}")
            
            if attempt < max_retries:
                # Calculate wait time with exponential backoff
                wait_time = min(2 ** attempt, 60)  # Cap at 60 seconds
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
                # Optional: Clear any partial downloads
                try:
                    if 'info' in locals():
                        temp_filename = ydl_opts.get('outtmpl', {}).get('default', '%(title)s.%(ext)s')
                        if isinstance(temp_filename, str):
                            temp_file = temp_filename % info
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                print(f"🧹 Cleared partial download: {temp_file}")
                except Exception as cleanup_error:
                    print(f"Note: Could not clean up partial files: {cleanup_error}")
            else:
                print(f"❌ All {max_retries} attempts failed for URL: {url}")
                return None
    
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

def get_ydl_opts(base_directory, convert_for_tg):
    """Get yt-dlp options with DUB-focused format selection"""
    ydl_opts = {
        'outtmpl': os.path.join(base_directory, '%(series)s', '%(series)s - %(episode_number)s - %(episode)s.%(ext)s'),
        'verbose': True,
        # Use a format selector that prioritizes DUB versions with resolution preference
        'format': 'best[height<=360]/best[height<=480]/best[height<=720]/best[height<=1080]/best',
        'concurrent_fragments': 5,
        'fragment_retries': 10,
        'ratelimit': None,
        'throttledratelimit': None,
        'retries': 10,
        'file_access_retries': 5,
        'skip_unavailable_fragments': True,
        'continuedl': True,
        'noprogress': False,
        'http_chunk_size': 10485760,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://hianime.to/'
        },
        'nocheckcertificate': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'srt',
        'embed-subs': True,
        # REMOVE the postprocessors to avoid conflicts with our custom conversion
        'postprocessors': [],
    }

    # Use aria2c for much faster downloads if available
    if check_aria2():
        print("✓ aria2c found - using for accelerated downloads")
        ydl_opts['external_downloader'] = 'aria2c'
        ydl_opts['external_downloader_args'] = [
            '--max-connection-per-server=16',
            '--split=16',
            '--min-split-size=1M',
            '--file-allocation=none'
        ]
    else:
        print("ℹ aria2c not found - using built-in downloader (install aria2 for better speeds)")
    
    return ydl_opts

def main():
    # Test speed first
    print("Running speed test...")
    speed = speed_test()
    if speed < 500:  # If less than 500 KB/s
        print("⚠ Warning: Your connection speed seems slow for downloads")
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Please enter the HiAnime URL to download: ")

    # Get the directory where the Python script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Use the script directory itself as base directory (not parent)
    base_directory = script_directory
    
    print(f"Using base directory: {base_directory}")
    
    # Create base directory if it doesn't exist (though it should)
    os.makedirs(base_directory, exist_ok=True)

    # Check if user wants Telegram conversion
    convert_for_tg = True
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['false', '0', 'no', 'n']:
            convert_for_tg = False

    # Use the new function to get ydl_opts
    ydl_opts = get_ydl_opts(base_directory, convert_for_tg)

    try:
        # First, check if it's a playlist or single video
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if 'entries' in info:
            # It's a playlist
            print(f"Found playlist with {len(info['entries'])} videos")
            all_downloaded_files = []
            failed_videos = []
            
            for i, entry in enumerate(info['entries'], 1):
                if entry:  # Some entries might be None
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if video_url:
                        print(f"\n--- Processing video {i}/{len(info['entries'])} ---")
                        result_files = download_video_with_subtitles_with_retry(
                            video_url, ydl_opts, convert_for_tg, base_directory, max_retries=10
                        )
                        
                        if result_files:
                            all_downloaded_files.extend(result_files)
                            print(f"✓ Successfully processed video {i}")
                        else:
                            print(f"✗ Failed to process video {i} after 10 attempts")
                            failed_videos.append((i, video_url))
                            continue
                            
                        # Add delay between downloads to avoid being blocked
                        if i < len(info['entries']):
                            print("Waiting 3 seconds before next download...")
                            time.sleep(3)
                    else:
                        print(f"Could not get URL for video {i}")
                        failed_videos.append((i, "No URL"))
                else:
                    print(f"Empty entry at position {i}")
                    failed_videos.append((i, "Empty entry"))
                    
            print(f"\n🎉 Playlist download completed!")
            print(f"Successfully processed: {len(all_downloaded_files)} files")
            print(f"Failed: {len(failed_videos)} videos")
            print(f"Files downloaded to: {base_directory}")
            
            if failed_videos:
                print("\n❌ Failed videos:")
                for video_num, video_url in failed_videos:
                    print(f"  - Video {video_num}: {video_url}")
            
            for file in all_downloaded_files:
                print(f"  - {file}")
            
        else:
            # It's a single video
            print("Downloading single video...")
            result_files = download_video_with_subtitles_with_retry(url, ydl_opts, convert_for_tg, base_directory, max_retries=10)
            if result_files:
                print(f"🎉 Single video download completed!")
                print(f"Files downloaded to: {base_directory}")
                for file in result_files:
                    print(f"  - {file}")
            else:
                print("❌ Failed to download video after 10 attempts")
        
        # Run comb.py after all downloads are complete
        run_comb_script()
                
    except Exception as e:
        print(f"An error occurred: {e}")
        # Even if there was an error, try to run comb.py if we downloaded some files
        run_comb_script()

if __name__ == "__main__":
    main()
