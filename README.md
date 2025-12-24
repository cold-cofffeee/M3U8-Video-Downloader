# 🎬 ACS Video Downloader

A minimalistic web application designed to download and convert HLS/m3u8 video streams (commonly used for anti-piracy protection on CDN platforms) to MP4 format with the highest available quality.

## 🎯 Purpose

This tool is designed for content creators who need to download their own video content from CDN platforms that use m3u8 segmented streaming. It solves the problem of retrieving your own videos that are stored in segmented HLS format on platforms like BunnyCDN, where videos are broken into multiple `.dts` or `.ts` segments for streaming protection.

**Use Case**: You upload videos to a CDN platform, and they convert them to m3u8/HLS format for anti-piracy. Now you need to download your own content in standard MP4 format for backup or other purposes.

## ✨ Features

- 🌐 Simple, clean web interface
- 🎯 Automatically finds the highest quality video stream
- 🎵 Combines video and audio tracks (if separated)
- 📦 Downloads and converts to MP4 format
- 🚀 Fast conversion using FFmpeg (stream copy, no re-encoding)
- 📥 Built-in download manager
- 🔍 Smart URL detection (supports m3u8 URLs, segment URLs, or base URLs)
- 💾 Local FFmpeg included (no separate installation needed)

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Git (with Git LFS support for ffmpeg binaries)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ACS-Video-Downloader.git
cd ACS-Video-Downloader
```

**Note**: This repository uses Git LFS (Large File Storage) to handle FFmpeg binaries (200MB+). Make sure you have Git LFS installed:
```bash
git lfs install
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

Then open your browser at: **http://localhost:5000**

## 📖 How to Use

### Finding the Video URL from Browser

When you play your video on a CDN platform, you can extract the necessary URL from your browser's Developer Tools:

1. **Open Developer Tools**: Press `F12` in your browser
2. **Navigate to Network Tab**: Click on the "Network" tab
3. **Play the Video**: Start playing your video
4. **Find Video Requests**: Look for requests with extensions like:
   - `.m3u8` (playlist files)
   - `.ts` or `.dts` (video segments)
5. **Copy the URL**: Right-click on any of these requests and copy the URL

#### Example from BunnyCDN:

From the Network tab, you might see requests like:
```
https://vz-eb59df21-3f5.b-cdn.net/32c7c9cf-b006-475f-bc4c-82db42899982/720p/video172.dts
```

**You can use any of these URL formats:**
- Full segment URL: `https://domain.com/video-id/720p/video172.dts`
- Playlist URL: `https://domain.com/video-id/playlist.m3u8`
- Master playlist: `https://domain.com/video-id/master.m3u8`
- Base URL: `https://domain.com/video-id/`

### Downloading the Video

1. Paste the copied URL into the web interface
2. Click **"Download Video"**
3. Wait for the download and conversion to complete
4. Once finished, click **Download** from the "Downloaded Videos" section
5. Your MP4 file is ready!

## 🔧 How It Works

1. **URL Detection**: The app intelligently parses your input URL to find the video ID
2. **Playlist Discovery**: Automatically locates the master m3u8 playlist
3. **Quality Selection**: Analyzes available streams and selects the highest quality (based on bandwidth)
4. **Download**: Uses FFmpeg to download all video segments
5. **Conversion**: Combines segments into a single MP4 file (stream copy mode - no quality loss)
6. **Audio Merging**: If audio comes separately, it's automatically combined with video

## 📂 File Structure

```
ACS-Video-Downloader/
├── app.py                 # Main Flask application
├── setup_ffmpeg.py        # FFmpeg setup helper (legacy)
├── requirements.txt       # Python dependencies
├── ffmpeg/               # Local FFmpeg binaries (Git LFS)
│   └── bin/
│       ├── ffmpeg.exe    # FFmpeg executable (207MB)
│       ├── ffplay.exe    # FFplay executable
│       └── ffprobe.exe   # FFprobe executable
├── templates/
│   └── index.html        # Web interface
├── downloads/            # Downloaded videos (auto-created)
├── .gitattributes        # Git LFS configuration
└── .gitignore           # Git ignore rules
```

## 🛠️ Technical Details

- **Backend**: Python Flask
- **Video Processing**: FFmpeg (included, no installation required)
- **Streaming Protocol**: HLS (HTTP Live Streaming)
- **Format Support**: m3u8 playlists, MPEG-TS segments (.ts, .dts)
- **Output Format**: MP4 with H.264 video and AAC audio
- **Conversion Method**: Stream copy (no re-encoding for maximum speed and quality preservation)

## 🔍 Supported CDN Platforms

While designed for any HLS-based CDN, it works particularly well with:
- BunnyCDN Video Stream
- Cloudflare Stream
- AWS CloudFront with HLS
- Any platform serving m3u8/HLS content

## 🐙 Git LFS Information

This repository uses **Git LFS (Large File Storage)** to manage FFmpeg binaries, which are over 200MB each. This allows GitHub to accept files larger than the standard 100MB limit.

### For Cloning Users:

If you clone this repository and the ffmpeg binaries are not downloading automatically:

```bash
# Install Git LFS
git lfs install

# Pull LFS files
git lfs pull
```

### For Contributors:

FFmpeg binaries in `ffmpeg/bin/*.exe` are automatically tracked by Git LFS via [.gitattributes](.gitattributes).

## ⚠️ Troubleshooting

## ⚠️ Troubleshooting

### FFmpeg binaries missing after clone
If the `ffmpeg/bin/` folder is empty:
```bash
git lfs install
git lfs pull
```

### "FFmpeg not found" error
Ensure the `ffmpeg/bin/ffmpeg.exe` file exists and is not corrupted. Re-clone the repository with Git LFS.

### "Error parsing m3u8"
- Verify you're using a valid URL from the browser Network tab
- Try using the full segment URL instead of a partial URL
- Check if the video requires authentication/cookies

### Download is very slow
This is normal for large videos. HLS streams are downloaded segment-by-segment, then combined. A 1GB video may take several minutes depending on your internet connection.

### "Permission denied" errors
Run the application with appropriate permissions. On Windows, you may need to run as administrator if the `downloads/` folder creation fails.

### Videos won't play after download
Ensure the download completed successfully. Check the file size - if it's very small (few KB), the download likely failed.

## 📝 Legal Notice

**Important**: This tool is intended for downloading your own content that you have legally uploaded to CDN platforms. 

- ✅ Use for backing up your own videos
- ✅ Use for retrieving content you legally own
- ❌ Do not use to pirate or download copyrighted content you don't own
- ❌ Respect the terms of service of the platforms you use

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

Free to use for personal and educational purposes.

---

**Made for content creators who need to retrieve their own videos from HLS/m3u8 CDN platforms.**
