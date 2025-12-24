from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import requests
import m3u8
import re
import uuid
import threading
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Create downloads directory
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Store download progress and status
download_jobs = {}

class DownloadJob:
    def __init__(self, job_id):
        self.job_id = job_id
        self.status = 'downloading'  # downloading, complete, error, cancelled
        self.progress = 0
        self.message = 'Starting...'
        self.cancelled = False
        self.filename = None
        self.error = None
        self.created_at = datetime.now()
        self.temp_dir = None  # Track temp directory for cleanup

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
    
    # Try to construct from segment URL (like .dts or .ts files)
    if ('.dts' in base_url or '.ts' in base_url) and '/video' in base_url:
        # Remove segment filename and quality folder to get base
        # From: https://domain.com/video-id/720p/video180.dts
        # To: https://domain.com/video-id/playlist.m3u8
        base = re.sub(r'/\d+p/video\d+\.(dts|ts).*$', '', base_url)
        possible_urls.extend([
            f"{base}/playlist.m3u8",
            f"{base}/master.m3u8",
        ])
        
        # Also try keeping the quality folder
        base_with_quality = re.sub(r'/video\d+\.(dts|ts).*$', '', base_url)
        possible_urls.append(f"{base_with_quality}/playlist.m3u8")
    
    # Try common patterns with video ID
    if video_id:
        base_domain = re.search(r'(https?://[^/]+)', base_url)
        if base_domain:
            domain = base_domain.group(1)
            possible_urls.extend([
                f"{domain}/{video_id}/playlist.m3u8",
                f"{domain}/{video_id}/master.m3u8",
            ])
    
    # Test each possible URL with proper headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://iframe.mediadelivery.net/',
        'Origin': 'https://iframe.mediadelivery.net'
    }
    
    for url in possible_urls:
        try:
            print(f"Trying: {url}")
            response = requests.head(url, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✓ Found playlist: {url}")
                return url
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    
    print(f"⚠ Could not find playlist, returning original URL")
    return base_url

def get_best_quality_stream(m3u8_url):
    """Parse m3u8 and find the highest quality stream"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://iframe.mediadelivery.net/',
            'Origin': 'https://iframe.mediadelivery.net'
        }
        
        response = requests.get(m3u8_url, headers=headers, timeout=10)
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

def download_video_with_progress(url, output_filename, job):
    """Download and convert m3u8 stream to MP4 by manually downloading segments with progress tracking"""
    ffmpeg_path = get_ffmpeg_path()
    
    if not ffmpeg_path:
        job.status = 'error'
        job.error = "FFmpeg not found"
        return False, "FFmpeg not found. Please install ffmpeg or place ffmpeg.exe in the app directory."
    
    try:
        # Find the actual m3u8 URL
        job.message = "Finding playlist URL..."
        job.progress = 5
        m3u8_url = find_m3u8_url(url)
        
        if job.cancelled:
            job.status = 'cancelled'
            return False, "Download cancelled"
        
        # Get the best quality stream
        job.message = "Selecting best quality stream..."
        job.progress = 10
        best_stream_url = get_best_quality_stream(m3u8_url)
        
        print(f"Downloading from: {best_stream_url}")
        
        # Prepare headers for requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Referer': 'https://iframe.mediadelivery.net/',
            'Origin': 'https://iframe.mediadelivery.net',
            'Accept': '*/*'
        }
        
        # Download and parse the playlist
        job.message = "Loading playlist..."
        response = requests.get(best_stream_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        playlist = m3u8.loads(response.text)
        
        if not playlist.segments:
            job.status = 'error'
            job.error = "No video segments found in playlist"
            return False, "No video segments found in playlist"
        
        # Create temp directory for segments
        temp_dir = DOWNLOADS_DIR / f'temp_segments_{job.job_id}'
        temp_dir.mkdir(exist_ok=True)
        job.temp_dir = temp_dir  # Store for cleanup
        
        # Base URL for resolving relative segment URLs
        base_url = best_stream_url.rsplit('/', 1)[0]
        
        total_segments = len(playlist.segments)
        print(f"Found {total_segments} segments to download")
        
        # Download each segment
        segment_files = []
        for i, segment in enumerate(playlist.segments):
            if job.cancelled:
                job.status = 'cancelled'
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, "Download cancelled"
            
            segment_url = segment.uri if segment.uri.startswith('http') else f"{base_url}/{segment.uri}"
            segment_file = temp_dir / f"segment_{i:04d}.ts"
            
            # Update progress (15% to 85% for downloading)
            progress = 15 + (70 * (i / total_segments))
            job.progress = progress
            job.message = f"Downloading segment {i+1}/{total_segments}..."
            print(f"Downloading segment {i+1}/{total_segments}...")
            
            # Retry logic for failed downloads
            max_retries = 3
            for retry in range(max_retries):
                try:
                    seg_response = requests.get(segment_url, headers=headers, timeout=30)
                    seg_response.raise_for_status()
                    
                    # Validate segment has content
                    if len(seg_response.content) == 0:
                        raise ValueError("Empty segment received")
                    
                    with open(segment_file, 'wb') as f:
                        f.write(seg_response.content)
                    
                    # Verify file was written
                    if not segment_file.exists() or segment_file.stat().st_size == 0:
                        raise ValueError("Segment file not written properly")
                    
                    break  # Success, exit retry loop
                except Exception as e:
                    if retry == max_retries - 1:
                        # Last retry failed
                        raise Exception(f"Failed to download segment {i+1} after {max_retries} attempts: {str(e)}")
                    print(f"Retry {retry+1}/{max_retries} for segment {i+1}...")
                    import time
                    time.sleep(1)  # Wait before retry
            
            segment_files.append(segment_file)
        
        if job.cancelled:
            job.status = 'cancelled'
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False, "Download cancelled"
        
        job.progress = 90
        job.message = "Combining segments with FFmpeg..."
        print("All segments downloaded, combining with FFmpeg...")
        
        # Create concat file for FFmpeg (use forward slashes for compatibility)
        concat_file = temp_dir / 'concat.txt'
        with open(concat_file, 'w', encoding='utf-8') as f:
            for seg_file in segment_files:
                # Convert Windows path to forward slashes and escape for FFmpeg
                path_str = str(seg_file.absolute()).replace('\\', '/')
                f.write(f"file '{path_str}'\n")
        
        # Debug: Print concat file contents
        print(f"Concat file location: {concat_file}")
        print(f"Number of segments: {len(segment_files)}")
        
        # Verify all segment files exist
        missing_files = [f for f in segment_files if not f.exists()]
        if missing_files:
            error_msg = f"Missing {len(missing_files)} segment files"
            job.status = 'error'
            job.error = error_msg
            print(f"Error: {error_msg}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False, error_msg
        
        # Use FFmpeg to concatenate segments
        output_path = DOWNLOADS_DIR / output_filename
        cmd = [
            ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result.returncode == 0 and output_path.exists():
            job.progress = 100
            job.status = 'complete'
            job.message = "Download complete!"
            job.filename = output_filename
            print(f"✓ Video saved to: {output_path}")
            return True, str(output_path)
        else:
            # Extract only the relevant error message (last few lines)
            stderr_lines = result.stderr.strip().split('\n') if result.stderr else []
            # Get last 5 lines or less
            error_lines = stderr_lines[-5:] if len(stderr_lines) > 5 else stderr_lines
            error_msg = '\n'.join(error_lines) if error_lines else "Unknown FFmpeg error"
            
            job.status = 'error'
            job.error = error_msg
            print(f"FFmpeg error (full): {result.stderr}")
            print(f"FFmpeg error (summary): {error_msg}")
            return False, error_msg
            
    except Exception as e:
        job.status = 'error'
        job.error = str(e)
        print(f"Download error: {e}")
        # Cleanup temp directory on error
        if job.temp_dir and job.temp_dir.exists():
            import shutil
            shutil.rmtree(job.temp_dir, ignore_errors=True)
        return False, str(e)

def download_thread(url, output_filename, job_id):
    """Background thread for downloading"""
    try:
        job = download_jobs.get(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return
        download_video_with_progress(url, output_filename, job)
    except Exception as e:
        print(f"Fatal error in download thread: {e}")
        if job_id in download_jobs:
            job = download_jobs[job_id]
            job.status = 'error'
            job.error = f"Unexpected error: {str(e)}"

def cleanup_old_jobs():
    """Remove jobs older than 1 hour to prevent memory leaks"""
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(hours=1)
    
    jobs_to_remove = []
    for job_id, job in download_jobs.items():
        if job.created_at < cutoff_time:
            # Cleanup temp directory if exists
            if job.temp_dir and job.temp_dir.exists():
                import shutil
                shutil.rmtree(job.temp_dir, ignore_errors=True)
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        del download_jobs[job_id]
    
    if jobs_to_remove:
        print(f"Cleaned up {len(jobs_to_remove)} old jobs")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    # Cleanup old jobs (older than 1 hour)
    cleanup_old_jobs()
    
    # Generate job ID and output filename
    job_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"video_{timestamp}.mp4"
    
    # Create job
    job = DownloadJob(job_id)
    download_jobs[job_id] = job
    
    # Start download in background thread
    thread = threading.Thread(target=download_thread, args=(url, output_filename, job_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id
    })

@app.route('/progress/<job_id>')
def progress(job_id):
    job = download_jobs.get(job_id)
    if not job:
        return jsonify({'status': 'error', 'message': 'Job not found'})
    
    return jsonify({
        'status': job.status,
        'progress': job.progress,
        'message': job.message,
        'filename': job.filename,
        'error': job.error
    })

@app.route('/cancel/<job_id>', methods=['POST'])
def cancel(job_id):
    job = download_jobs.get(job_id)
    if job:
        job.cancelled = True
        job.status = 'cancelled'
    return jsonify({'success': True})

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
    # Cleanup any abandoned temp directories from previous runs
    import shutil
    for temp_dir in DOWNLOADS_DIR.glob('temp_segments_*'):
        print(f"Cleaning up abandoned temp directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)
    
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
