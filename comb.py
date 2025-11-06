import os
import re
import subprocess
import shutil
import tempfile
import sys

def extract_episode_number(filename):
    """Extract episode number from filename"""
    patterns = [
        r'[Ee]pisode\s*(\d+)',
        r'[Ee]p\s*(\d+)',
        r'\s-\s(\d+)\s-',
        r'\s(\d+)\s*[-_]',
        r'\[(\d+)\]',
        r'\b(\d{1,3})\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            episode_num = int(match.group(1))
            if 1 <= episode_num <= 999:
                return episode_num
    return None

def get_file_extension(filename):
    """Get file extension"""
    return os.path.splitext(filename)[1]

def is_video_file(filename):
    """Check if file is a video file"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def is_subtitle_file(filename):
    """Check if file is a subtitle file"""
    subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
    return any(filename.lower().endswith(ext) for ext in subtitle_extensions)

def find_matching_subtitle(video_file, subtitle_files, episode_num):
    """Find subtitle file that matches the video file by episode number"""
    for sub_file in subtitle_files:
        sub_episode = extract_episode_number(sub_file)
        if sub_episode == episode_num:
            return sub_file
    return None

def embed_subtitle(video_path, subtitle_path, output_path):
    """Embed subtitle into video using FFmpeg"""
    try:
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            print("  ❌ FFmpeg not found! Please install FFmpeg and add it to PATH")
            return False
        
        # For MP4 files with WebVTT subtitles, use this command [citation:1][citation:2]
        cmd = [
            'ffmpeg',
            '-i', video_path,          # Input video
            '-i', subtitle_path,       # Input subtitle (WebVTT)
            '-c:v', 'copy',           # Copy video stream (no re-encoding)
            '-c:a', 'copy',           # Copy audio stream (no re-encoding)
            '-c:s', 'mov_text',       # Convert WebVTT to mov_text for MP4 compatibility
            '-map', '0',              # Map video and audio from first input
            '-map', '1',              # Map subtitle from second input
            '-metadata:s:s:0', 'language=eng',  # Set subtitle language to English
            '-y',                     # Overwrite output file if exists
            output_path
        ]
        
        print(f"  🔄 Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode == 0:
            print(f"  ✅ Successfully embedded subtitles: {os.path.basename(output_path)}")
            return True
        else:
            print(f"  ❌ FFmpeg error: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ FFmpeg failed: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ❌ Error embedding subtitles: {str(e)}")
        return False

def process_folder(folder_path):
    """Process all video files in a folder and embed subtitles"""
    try:
        files = os.listdir(folder_path)
        
        # Separate video and subtitle files
        video_files = [f for f in files if is_video_file(f) and os.path.isfile(os.path.join(folder_path, f))]
        subtitle_files = [f for f in files if is_subtitle_file(f) and os.path.isfile(os.path.join(folder_path, f))]
        
        print(f"  📹 Found {len(video_files)} video files")
        print(f"  📝 Found {len(subtitle_files)} subtitle files")
        
        processed_count = 0
        kept_videos = []  # Track the embedded videos we're keeping
        
        # Process each video file
        for video_file in video_files:
            video_path = os.path.join(folder_path, video_file)
            episode_num = extract_episode_number(video_file)
            
            if episode_num is None:
                print(f"  ❌ Could not extract episode number from: {video_file}")
                continue
            
            # Find matching subtitle
            subtitle_file = find_matching_subtitle(video_file, subtitle_files, episode_num)
            
            if subtitle_file is None:
                print(f"  ❌ No matching subtitle found for: {video_file}")
                continue
            
            subtitle_path = os.path.join(folder_path, subtitle_file)
            
            # Create output filename with temporary name first
            temp_output = os.path.join(folder_path, f"temp_episode_{episode_num:02d}{get_file_extension(video_file)}")
            final_output_filename = f"Episode {episode_num:02d}{get_file_extension(video_file)}"
            final_output_path = os.path.join(folder_path, final_output_filename)
            
            print(f"  🎬 Processing: {video_file}")
            print(f"  📝 With subtitle: {subtitle_file}")
            print(f"  💾 Output: {final_output_filename}")
            
            # Embed subtitle to temporary file first
            if embed_subtitle(video_path, subtitle_path, temp_output):
                # Delete original files
                os.remove(video_path)
                os.remove(subtitle_path)
                
                # Rename temporary file to final name
                os.rename(temp_output, final_output_path)
                
                processed_count += 1
                kept_videos.append(final_output_filename)
            
            print("-" * 40)
        
        return processed_count
                
    except Exception as e:
        print(f"  ❌ Error processing folder {folder_path}: {str(e)}")
        return 0

def run_1_script():
    """Run the 1.py script after all processing is complete"""
    try:
        print("\n" + "="*60)
        print("All subtitle embedding completed. Running 1.py...")
        print("="*60)
        
        # Check if 1.py exists in the current directory
        if os.path.exists("1.py"):
            result = subprocess.run([sys.executable, "1.py"], capture_output=True, text=True)
            print("1.py output:")
            print(result.stdout)
            if result.stderr:
                print("1.py errors:")
                print(result.stderr)
            print("✅ 1.py execution completed")
        else:
            print("❌ 1.py not found in current directory")
            
    except Exception as e:
        print(f"❌ Error running 1.py: {e}")

def main():
    # Get the directory where this script is located
    target_directory = os.path.dirname(os.path.abspath(__file__))
    
    print(f"📁 Scanning script directory: {target_directory}")
    print("=" * 60)
    
    # Check if directory exists
    if not os.path.exists(target_directory):
        print(f"❌ Error: Directory {target_directory} does not exist!")
        return
    
    # Get all items in the directory
    items = os.listdir(target_directory)
    
    # Filter only directories (exclude files)
    folders = [item for item in items if os.path.isdir(os.path.join(target_directory, item))]
    
    if not folders:
        print("❌ No folders found in the directory!")
        return
    
    print(f"📂 Found {len(folders)} folder(s): {', '.join(folders)}")
    print("=" * 60)
    
    total_processed = 0
    
    # Process each folder
    for folder in folders:
        folder_path = os.path.join(target_directory, folder)
        print(f"\n🔄 Processing folder: {folder}")
        print("-" * 50)
        
        processed_count = process_folder(folder_path)
        total_processed += processed_count
        
        if processed_count == 0:
            print(f"  ℹ️  No files were processed in '{folder}'")
    
    print("\n" + "=" * 60)
    print("🎉 Process completed!")
    print(f"📊 Total videos with embedded subtitles: {total_processed}")
    
    if total_processed > 0:
        print("\n💡 Note:")
        print("• Original video and subtitle files have been deleted")
        print("• Only videos with embedded subtitles remain")
        print("• Files are renamed to: Episode XX.ext")
        print("• You can now upload the videos directly!")
    else:
        print("\n❌ No videos were processed. Please check:")
        print("• FFmpeg is installed and in PATH")
        print("• Video and subtitle files have matching episode numbers")
        print("• File formats are supported")
    
    # Run 1.py after all processing is complete
    run_1_script()

if __name__ == "__main__":
    main()
