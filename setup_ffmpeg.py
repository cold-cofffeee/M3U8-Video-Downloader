"""
FFmpeg Setup Helper
This script helps download a portable version of ffmpeg if it's not already installed.
"""
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_ffmpeg_windows():
    """Download portable ffmpeg for Windows"""
    print("Downloading portable FFmpeg for Windows...")
    
    # Using gyan.dev builds which are commonly used
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg.zip"
    
    print(f"Downloading from: {url}")
    print("This may take a few minutes...")
    
    try:
        # Download with progress
        urllib.request.urlretrieve(url, zip_path)
        print("✓ Download complete!")
        
        print("Extracting ffmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temp directory
            temp_dir = "temp_ffmpeg"
            zip_ref.extractall(temp_dir)
            
            # Find ffmpeg.exe in the extracted files
            for root, dirs, files in os.walk(temp_dir):
                if 'ffmpeg.exe' in files:
                    src = os.path.join(root, 'ffmpeg.exe')
                    shutil.copy2(src, 'ffmpeg.exe')
                    print(f"✓ Copied ffmpeg.exe to current directory")
                    break
            
            # Cleanup
            shutil.rmtree(temp_dir)
            os.remove(zip_path)
            
        print("✓ FFmpeg setup complete!")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading ffmpeg: {e}")
        print("\nManual installation instructions:")
        print("1. Download from: https://www.gyan.dev/ffmpeg/builds/")
        print("2. Extract the archive")
        print("3. Copy ffmpeg.exe to this directory")
        return False

def check_ffmpeg():
    """Check if ffmpeg is available"""
    # Check system PATH
    if shutil.which('ffmpeg'):
        print("✓ FFmpeg found in system PATH")
        return True
    
    # Check local directory
    if Path('ffmpeg.exe').exists():
        print("✓ FFmpeg found in current directory")
        return True
    
    return False

def main():
    print("=" * 50)
    print("FFmpeg Setup Helper")
    print("=" * 50)
    
    if check_ffmpeg():
        print("\nFFmpeg is already installed! No action needed.")
        return
    
    print("\n✗ FFmpeg not found on your system.")
    
    if os.name == 'nt':  # Windows
        response = input("\nWould you like to download portable FFmpeg? (y/n): ")
        if response.lower() == 'y':
            download_ffmpeg_windows()
        else:
            print("\nManual installation instructions:")
            print("1. Download from: https://www.gyan.dev/ffmpeg/builds/")
            print("2. Extract the archive")
            print("3. Copy ffmpeg.exe to this directory")
    else:
        print("\nPlease install ffmpeg using your package manager:")
        print("Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("macOS: brew install ffmpeg")
        print("Or download from: https://ffmpeg.org/download.html")

if __name__ == '__main__':
    main()
