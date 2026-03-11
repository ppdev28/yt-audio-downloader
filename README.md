# YouTube Audio Downloader

This script allows you to download the audio from a YouTube video in MP3 format.

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

To download the audio from a YouTube video, use the `run.sh` script:

```bash
./run.sh <YOUTUBE_URL>
```

Replace `<YOUTUBE_URL>` with the URL of the YouTube video you want to download. The MP3 file will be saved in the `canciones` folder.

This script will automatically use the Python interpreter from the virtual environment, so you don't need to activate it manually before running it.
