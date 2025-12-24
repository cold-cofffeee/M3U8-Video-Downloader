from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import requests
import m3u8
import re
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Create downloads directory
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

def get_ffmpeg_path():
    """Get path to local ffmpeg executable"""
    # Use local ffmpeg from ffmpeg/bin directory
    if os.name == 'nt':  # Windows
        local_ffmpeg = Path('ffmpeg/bin/ffmpeg.exe')
    else:  # Linux/Mac
        local_ffmpeg = Path('ffmpeg/bin/ffmpeg')
    
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    
    return None

def find_m3u8_url(base_url, video_id=None):
    """Try to find the master m3u8 playlist URL"""
    possible_urls = []
    
    # If it's already an m3u8 URL
    if base_url.endswith('.m3u8'):
        return base_url
    
    # Extract video ID from URL if present
    if not video_id:
        match = re.search(r'([a-f0-9\-]{36})', base_url)
        if match:
            video_id = match.group(1)
    
    # Try common patterns
    if video_id:
        base_domain = re.search(r'(https?://[^/]+)', base_url)
        if base_domain:
            domain = base_domain.group(1)
            possible_urls = [
                f"{domain}/{video_id}/playlist.m3u8",
                f"{domain}/{video_id}/master.m3u8",
            ]
    
    # Try to construct from segment URL
    if '/video' in base_url and '.dts' in base_url:
        # Remove segment filename
        base = re.sub(r'/video\d+\.dts.*$', '', base_url)
        possible_urls.append(f"{base}/playlist.m3u8")
    
    # Test each possible URL
    for url in possible_urls:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except:
            continue
    
    return base_url

def get_best_quality_stream(m3u8_url):
    """Parse m3u8 and find the highest quality stream"""
    try:
        response = requests.get(m3u8_url, timeout=10)
        response.raise_for_status()
        
        playlist = m3u8.loads(response.text)
        
        # If it's a master playlist with multiple qualities
        if playlist.playlists:
            # Sort by bandwidth (highest first)
            best_playlist = max(playlist.playlists, key=lambda p: p.stream_info.bandwidth if p.stream_info.bandwidth else 0)
            
            # Construct full URL for the best quality playlist
            if best_playlist.uri.startswith('http'):
                return best_playlist.uri
            else:
                base_url = m3u8_url.rsplit('/', 1)[0]
                return f"{base_url}/{best_playlist.uri}"
        
        # If it's already a media playlist
        return m3u8_url
        
    except Exception as e:
        print(f"Error parsing m3u8: {e}")
        return m3u8_url

def download_video(url, output_filename):
    """Download and convert m3u8 stream to MP4 using ffmpeg"""
    ffmpeg_path = get_ffmpeg_path()
    
    if not ffmpeg_path:
        return False, "FFmpeg not found. Please install ffmpeg or place ffmpeg.exe in the app directory."
    
    try:
        # Find the actual m3u8 URL
        m3u8_url = find_m3u8_url(url)
        
        # Get the best quality stream
        best_stream_url = get_best_quality_stream(m3u8_url)
        
        output_path = DOWNLOADS_DIR / output_filename
        
        # Prepare headers to bypass CDN restrictions (403 Forbidden)
        # These headers mimic a browser request
        headers = (
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36\r\n"
            "Referer: https://iframe.mediadelivery.net/\r\n"
            "Origin: https://iframe.mediadelivery.net\r\n"
            "Accept: */*\r\n"
        )
        
        # Use ffmpeg to download and convert with proper headers
        cmd = [
            ffmpeg_path,
            '-headers', headers,  # Add browser-like headers to bypass 403
            '-i', best_stream_url,
            '-c', 'copy',  # Copy without re-encoding (faster)
            '-bsf:a', 'aac_adtstoasc',  # Fix AAC bitstream
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        print(f"Downloading from: {best_stream_url}")
        print(f"Command: {' '.join(cmd[:3])}... [URL and options]")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and output_path.exists():
            return True, str(output_path)
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            print(f"FFmpeg error: {error_msg}")
            return False, f"FFmpeg error: {error_msg}"
            
    except Exception as e:
        print(f"Download error: {e}")
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"video_{timestamp}.mp4"
    
    success, result = download_video(url, output_filename)
    
    if success:
        return jsonify({
            'success': True,
            'filename': output_filename,
            'path': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        })

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = DOWNLOADS_DIR / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/list-downloads')
def list_downloads():
    files = []
    for file in DOWNLOADS_DIR.glob('*.mp4'):
        files.append({
            'name': file.name,
            'size': f"{file.stat().st_size / (1024*1024):.2f} MB",
            'created': datetime.fromtimestamp(file.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(files)

if __name__ == '__main__':
    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        print(f"✓ FFmpeg found: {ffmpeg}")
    else:
        print("✗ FFmpeg not found in ffmpeg/bin/ folder!")
        print("Please ensure Git LFS has pulled the ffmpeg binaries.")
    
    print("\n" + "="*50)
    print("🎬 ACS Video Downloader")
    print("="*50)
    print("\n✓ Server starting...")
    print("✓ Open your browser at: http://localhost:5000\n")
    app.run(debug=True, port=5000)
