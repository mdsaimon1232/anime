def embed_subtitle(video_path, subtitle_path, output_path):
    """Embed subtitle into video using FFmpeg"""
    try:
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            print("  ❌ FFmpeg not found! Please install FFmpeg and add it to PATH")
            return False
        
        # For MP4 files with WebVTT subtitles, explicitly map only video, audio and subtitle streams
        # This excludes the problematic data stream (timed_id3)
        cmd = [
            'ffmpeg',
            '-i', video_path,          # Input video
            '-i', subtitle_path,       # Input subtitle (WebVTT)
            '-map', '0:v',            # Map only video from first input
            '-map', '0:a',            # Map only audio from first input  
            '-map', '1:s',            # Map only subtitle from second input
            '-c:v', 'copy',           # Copy video stream (no re-encoding)
            '-c:a', 'copy',           # Copy audio stream (no re-encoding)
            '-c:s', 'mov_text',       # Convert WebVTT to mov_text for MP4 compatibility
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
