import logging
import yt_dlp
from typing import Optional, Callable

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class YouTubeAudioDownloader:
    def __init__(self, output_path: str = "songs"):
        self.output_path = output_path
        self.ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{self.output_path}/%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [],  # Placeholder for progress hooks
        }

    def download_audio(self, url: str, progress_hook: Optional[Callable] = None) -> Optional[str]:
        try:
            opts = self.ydl_opts.copy()
            if progress_hook:
                opts["progress_hooks"] = [progress_hook]

            with yt_dlp.YoutubeDL(opts) as ydl:
                logger.info(f"Descargando: {url}")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename.rsplit(".", 1)[0] + ".mp3"
        except Exception as e:
            logger.error(f"Error en descarga: {e}")
            return None
