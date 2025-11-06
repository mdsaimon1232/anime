def embed_subtitle(video_path, subtitle_path, output_path):
    """Embed subtitle into video using FFmpeg"""
    try:
        # Check if ffmpeg is available
        if not shutil.which('ffmpeg'):
            print("  ❌ FFmpeg not found! Please install FFmpeg and add it to PATH")
            return False
        
        # First, let's check what streams are actually in the video file
        print(f"  🔍 Analyzing video file streams...")
        probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if probe_result.returncode != 0:
            print(f"  ❌ Could not analyze video file: {video_path}")
            return False
        
        # For MP4 files with WebVTT subtitles, use explicit stream mapping
        cmd = [
            'ffmpeg',
            '-i', video_path,          # Input video
            '-i', subtitle_path,       # Input subtitle (WebVTT)
            '-map', '0:v:0',          # Map first video stream from first input
            '-map', '0:a:0',          # Map first audio stream from first input  
            '-map', '1:s:0',          # Map first subtitle stream from second input
            '-c:v', 'copy',           # Copy video stream (no re-encoding)
            '-c:a', 'copy',           # Copy audio stream (no re-encoding)
            '-c:s', 'mov_text',       # Convert WebVTT to mov_text for MP4 compatibility
            '-metadata:s:s:0', 'language=eng',  # Set subtitle language to English
            '-y',                     # Overwrite output file if exists
            output_path
        ]
        
        print(f"  🔄 Running FFmpeg command...")
        print(f"  Command: {' '.join(cmd)}")
        
        # Run with timeout to prevent hanging
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"  ✅ Successfully embedded subtitles: {os.path.basename(output_path)}")
            # Verify the output file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                print(f"  ❌ Output file was not created or is empty")
                return False
        else:
            print(f"  ❌ FFmpeg failed with return code: {result.returncode}")
            print(f"  FFmpeg stderr: {result.stderr}")
            if result.stdout:
                print(f"  FFmpeg stdout: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ FFmpeg timed out after 5 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ FFmpeg process error: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ❌ Error embedding subtitles: {str(e)}")
        return False
