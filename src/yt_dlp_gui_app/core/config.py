import json
import logging
import os
import shlex
from dataclasses import dataclass, field, fields, asdict
from typing import List, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QStandardPaths

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Dataklass för applikationens konfiguration."""
    # Allmänt
    yt_dlp_path: Optional[str] = None
    ffmpeg_path: Optional[str] = None # NYTT FÄLT
    theme: str = "default"
    max_parallel_downloads: int = 3
    last_output_dir: Optional[str] = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    save_queue_on_exit: bool = True
    default_args: List[str] = field(default_factory=list)

    # Nedladdningsalternativ
    download_format: str = "bestvideo+bestaudio/best"
    write_thumbnail: bool = True
    extract_audio: bool = False
    audio_format: str = "mp3"
    embed_thumbnail: bool = False
    write_subs: bool = False
    sub_langs: str = "en,sv"

class ConfigManager(QObject):
    """Hanterar laddning och sparande av applikationskonfiguration."""
    config_changed = pyqtSignal()

    def __init__(self, config_filename: str = "config.json"):
        super().__init__()
        self.config_dir = self._get_config_dir()
        self.config_path = os.path.join(self.config_dir, config_filename)
        self.config = AppConfig()
        logger.info(f"Konfigurationsfil kommer att användas: {self.config_path}")

    def _get_config_dir(self) -> str:
        return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        
    def get_config(self) -> AppConfig:
        return self.config

    def load_config(self) -> None:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            known_keys = {f.name for f in fields(AppConfig)}
            filtered_data = {k: v for k, v in data.items() if k in known_keys}
            self.config = AppConfig(**filtered_data)
            logger.info("Konfiguration laddad från fil.")
        except FileNotFoundError:
            logger.warning("Konfigurationsfilen hittades inte. Skapar en ny med standardvärden.")
            self.save_config()
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Fel vid avkodning av konfigurationsfil: {e}. Använder standardkonfiguration.")
            self.config = AppConfig()
        self.config_changed.emit()

    def save_config(self) -> None:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=4)
            logger.info("Konfiguration sparad.")
            self.config_changed.emit()
        except IOError as e:
            logger.error(f"Kunde inte spara konfigurationsfilen: {e}")

    def set_last_output_dir(self, directory: str) -> None:
        self.config.last_output_dir = directory
        self.save_config()
