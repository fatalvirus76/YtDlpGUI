import logging
import os
from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from yt_dlp_gui_app.core.models import DownloadJob

logger = logging.getLogger(__name__)

class ThumbnailGenerator(QObject):
    """
    Använder FFmpeg för att generera en miniatyrbild från en videofil.
    """
    thumbnail_generated = pyqtSignal(str, str)  # job_id, thumbnail_path
    generation_failed = pyqtSignal(str)      # job_id

    def __init__(self, job: DownloadJob, ffmpeg_path: str, parent: QObject | None = None):
        super().__init__(parent)
        self.job = job
        self.ffmpeg_path = ffmpeg_path
        self.process = QProcess()
        self.process.finished.connect(self._on_finished)

    def generate(self) -> None:
        """Startar FFmpeg-processen för att skapa en miniatyrbild."""
        if not (self.job.output_path and self.job.final_filename):
            logger.warning(f"Kan inte generera miniatyrbild för jobb {self.job.id}: sökväg eller filnamn saknas.")
            self.generation_failed.emit(self.job.id)
            return

        video_path = os.path.join(self.job.output_path, self.job.final_filename)
        if not os.path.exists(video_path):
            logger.warning(f"Videofil hittades inte för att generera miniatyrbild: {video_path}")
            self.generation_failed.emit(self.job.id)
            return
            
        base_filename, _ = os.path.splitext(video_path)
        self.thumbnail_path = f"{base_filename}.jpg"

        # **FIX:** Ändrat från '-ss 10%' till '-ss 5' för bättre kompatibilitet.
        # Tar en bildruta 5 sekunder in i videon.
        args = [
            '-ss', '5',         # Sök till 5 sekunder in i videon
            '-i', video_path,   # Indatafil
            '-vframes', '1',    # Extrahera en bildruta
            '-q:v', '3',        # Bildkvalitet (1-5, lägre är bättre)
            '-vf', 'scale=128:-1', # Skala bredden till 128px, behåll proportioner
            '-y',               # Skriv över befintlig fil
            self.thumbnail_path
        ]

        logger.info(f"Genererar miniatyrbild för jobb {self.job.id} med kommandot: {self.ffmpeg_path} {' '.join(args)}")
        self.process.start(self.ffmpeg_path, args)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Körs när FFmpeg-processen är klar."""
        if exit_code == 0 and os.path.exists(self.thumbnail_path):
            logger.info(f"Miniatyrbild genererad för jobb {self.job.id}: {self.thumbnail_path}")
            self.thumbnail_generated.emit(self.job.id, self.thumbnail_path)
        else:
            error_output = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            logger.error(f"Misslyckades med att generera miniatyrbild för jobb {self.job.id}. Fel: {error_output}")
            self.generation_failed.emit(self.job.id)
