import logging
from PyQt6.QtCore import QObject, pyqtSignal
from yt_dlp_gui_app.core.config import ConfigManager
from yt_dlp_gui_app.core.job_manager import JobManager
from yt_dlp_gui_app.core.models import DownloadJob

logger = logging.getLogger(__name__)

class UIBridge(QObject):
    """Fungerar som en brygga mellan UI-komponenter och kärnlogiken."""
    queue_changed = pyqtSignal()
    history_changed = pyqtSignal()
    job_updated = pyqtSignal(str)
    config_changed = pyqtSignal()
    log_message = pyqtSignal(str, str)
    active_jobs_count_changed = pyqtSignal(int) # NY SIGNAL

    def __init__(self, job_manager: JobManager, config_manager: ConfigManager, parent: QObject | None = None):
        super().__init__(parent)
        self.job_manager = job_manager
        self.config_manager = config_manager
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.job_manager.queue_changed.connect(self.queue_changed)
        self.job_manager.history_changed.connect(self.history_changed)
        self.job_manager.job_updated.connect(self.job_updated)
        self.job_manager.active_jobs_count_changed.connect(self.active_jobs_count_changed) # Koppla signalen
        self.config_manager.config_changed.connect(self.config_changed)
        log_handler = QtLogHandler(self)
        log_handler.message_written.connect(self.on_log_message)
        logging.getLogger().addHandler(log_handler)

    def on_log_message(self, level: str, message: str) -> None:
        self.log_message.emit(level, message)

    def _build_args_from_config(self) -> list[str]:
        config = self.config_manager.get_config()
        args = []
        if config.download_format: args.extend(["-f", config.download_format])
        if config.write_thumbnail: args.append("--write-thumbnail")
        if config.embed_thumbnail: args.append("--embed-thumbnail")
        if config.extract_audio:
            args.append("-x")
            if config.audio_format: args.extend(["--audio-format", config.audio_format])
        if config.write_subs:
            args.append("--write-subs")
            if config.sub_langs: args.extend(["--sub-langs", config.sub_langs])
        args.extend(config.default_args)
        unique_args = []
        for arg in args:
            if arg not in unique_args:
                unique_args.append(arg)
        return unique_args

    def add_new_download(self, url: str, output_path: str) -> None:
        if not url.strip():
            logger.warning("Försökte lägga till en tom URL.")
            return
        args = self._build_args_from_config()
        urls = [u.strip() for u in url.split()]
        for u in urls:
            job = DownloadJob(url=u, output_path=output_path, args_list=args)
            self.job_manager.add_job(job)
        logger.info(f"Lade till {len(urls)} nya jobb i kön med argument: {args}")

    def save_queue_to_file(self, path: str):
        self.job_manager.export_jobs(path)

    def load_queue_from_file(self, path: str):
        try:
            self.job_manager.import_jobs(path)
        except Exception as e:
            logger.error(f"Kunde inte importera kö från {path}: {e}")

    def trigger_thumbnail_generation(self, job_id: str):
        self.job_manager.trigger_thumbnail_generation(job_id)

    def retry_job(self, job_id: str) -> None:
        self.job_manager.retry_job(job_id)

    def cancel_job(self, job_id: str) -> None: self.job_manager.cancel_job(job_id)
    def remove_job(self, job_id: str) -> None: self.job_manager.remove_job(job_id)
    def clear_history(self) -> None: self.job_manager.clear_history()
    def get_queue(self) -> list[DownloadJob]: return self.job_manager.queue
    def get_history(self) -> list[DownloadJob]: return self.job_manager.history
    def get_job(self, job_id: str) -> DownloadJob | None:
        job = self.job_manager.get_job_from_queue(job_id)
        return job if job else self.job_manager.get_job_from_history(job_id)

class QtLogHandler(logging.Handler, QObject):
    message_written = pyqtSignal(str, str)
    def __init__(self, parent: QObject | None = None) -> None:
        logging.Handler.__init__(self)
        QObject.__init__(self, parent)
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self.message_written.emit(record.levelname, message)
