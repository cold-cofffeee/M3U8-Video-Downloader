# 🎬 M3U8 Video Downloader

A minimalistic web application to download and convert HLS/m3u8 video streams to MP4 format with the highest available quality.

## Features

- ✨ Simple, clean web interface
- 🎯 Automatically finds the highest quality video stream
- 🎵 Combines video and audio tracks
- 📦 Downloads and converts to MP4 format
- 🚀 Fast conversion using ffmpeg (stream copy, no re-encoding)
- 📥 Built-in download manager
- 🔍 Smart URL detection (supports m3u8 URLs, segment URLs, or base URLs)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup FFmpeg

**Option A: Automatic (Windows)**
```bash
python setup_ffmpeg.py
```

**Option B: Manual Installation**

- **Windows**: Download from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) and place `ffmpeg.exe` in the app directory
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

### 3. Run the Application

```bash
python app.py
```

Then open your browser at: **http://localhost:5000**

## How to Use

### Finding the Video URL

1. Open your video in the browser
2. Press `F12` to open Developer Tools
3. Go to the **Network** tab
4. Play the video
5. Look for requests to `.m3u8`, `.ts`, or `.dts` files
6. Copy one of these URLs:
   - The `.m3u8` playlist URL (best option)
   - A video segment URL (like `video172.dts`)
   - The base URL containing the video ID

### Downloading

1. Paste the URL into the web interface
2. Click "Download Video"
3. Wait for the download and conversion to complete
4. Download the MP4 file from the "Downloaded Videos" section

## Supported URL Formats

The app intelligently handles various URL formats:

```
✓ https://domain.com/video-id/playlist.m3u8
✓ https://domain.com/video-id/master.m3u8
✓ https://domain.com/video-id/720p/video172.dts
✓ https://domain.com/video-id/
```

## Example URLs (from your case)

Based on your network logs, you can use URLs like:
```
https://vz-eb59df21-3f5.b-cdn.net/32c7c9cf-b006-475f-bc4c-82db42899982/720p/video172.dts
```

The app will automatically:
1. Extract the video ID
2. Find the playlist URL
3. Select the highest quality stream
4. Download and convert to MP4

## Technical Details

- **Backend**: Python Flask
- **Video Processing**: FFmpeg (stream copy mode for fast conversion)
- **Format Support**: HLS (m3u8), MPEG-TS segments
- **Output**: MP4 with H.264 video and AAC audio

## File Structure

```
acs/
├── app.py                 # Main Flask application
├── setup_ffmpeg.py        # FFmpeg setup helper
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web interface
└── downloads/            # Downloaded videos (auto-created)
```

## Troubleshooting

### "FFmpeg not found"
Run `python setup_ffmpeg.py` or manually install ffmpeg.

### "Error parsing m3u8"
Make sure you're using a valid playlist or segment URL from the network tab.

### Download is slow
This is normal for large videos. The app downloads all segments and combines them.

### "Permission denied" errors
Make sure you have write permissions in the app directory.

## Notes

- Downloaded videos are saved in the `downloads/` folder
- The app uses stream copy mode (no re-encoding) for maximum speed
- Highest available quality is automatically selected
- Audio and video are combined if they come separately

## License

Free to use for personal projects.
