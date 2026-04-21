# YouTube Audio Downloader

This script allows you to download the audio from a YouTube video in MP3 format.

## Download App (macOS, Windows, Linux)

Prebuilt executables are published in the repository Releases.

1. Open the [Releases](../../releases) page.
2. Download the file for your system:
   - `yt-audio-downloader-macos.tar.gz`
   - `yt-audio-downloader-linux.tar.gz`
   - `yt-audio-downloader-windows.zip`
3. Extract the file and run the executable:
   - macOS/Linux: `yt-audio-downloader`
   - Windows: `yt-audio-downloader.exe`

To generate new executables automatically, create and push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions builds all 3 binaries and uploads them to the new Release.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/youtube-discord-downloader.git
    cd youtube-discord-downloader
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
    (You can deactivate the virtual environment after installation by typing `deactivate`)

## Usage

To use the program, run `backend/main.py`:

```bash
python3 backend/main.py <YOUTUBE_URL>
```

Replace `<YOUTUBE_URL>` with the URL of the YouTube video you want to download. The MP3 file will be saved in the `downloads` folder.
