def embed_subtitle(video_path, subtitle_path, output_path):
    """Embed subtitle into video using FFmpeg - Alternative approach"""
    try:
        if not shutil.which('ffmpeg'):
            print("  ❌ FFmpeg not found! Please install FFmpeg and add it to PATH")
            return False
        
        # Alternative approach: Convert WebVTT to SRT first, then embed
        temp_srt = os.path.join(os.path.dirname(output_path), "temp_subtitle.srt")
        
        # Convert WebVTT to SRT
        convert_cmd = [
            'ffmpeg',
            '-i', subtitle_path,
            temp_srt,
            '-y'
        ]
        
        print(f"  🔄 Converting WebVTT to SRT...")
        convert_result = subprocess.run(convert_cmd, capture_output=True, text=True, timeout=60)
        
        if convert_result.returncode != 0:
            print(f"  ❌ Failed to convert WebVTT to SRT: {convert_result.stderr}")
            return False
        
        # Now embed the SRT subtitle
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', temp_srt,
            '-map', '0',
            '-map', '1',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'mov_text',
            '-metadata:s:s:0', 'language=eng',
            '-y',
            output_path
        ]
        
        print(f"  🔄 Running FFmpeg with SRT subtitle...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Clean up temporary SRT file
        if os.path.exists(temp_srt):
            os.remove(temp_srt)
        
        if result.returncode == 0:
            print(f"  ✅ Successfully embedded subtitles: {os.path.basename(output_path)}")
            return True
        else:
            print(f"  ❌ FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
