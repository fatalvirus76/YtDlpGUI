import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List
from PyQt6.QtCore import QObject, pyqtSignal, QProcess, QTimer, QStandardPaths
from yt_dlp_gui_app.core.config import ConfigManager
from yt_dlp_gui_app.core.models import DownloadJob, JobStatus
from yt_dlp_gui_app.core.yt_dlp_runner import YtDlpRunner
from yt_dlp_gui_app.core.thumbnail_generator import ThumbnailGenerator

logger = logging.getLogger(__name__)

class JobManager(QObject):
    """Hanterar kön, historiken och körningen av nedladdningsjobb."""
    queue_changed = pyqtSignal()
    history_changed = pyqtSignal()
    job_updated = pyqtSignal(str)
    active_jobs_count_changed = pyqtSignal(int)

    def __init__(self, config_manager: ConfigManager, parent: QObject | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.queue: List[DownloadJob] = []
        self.history: List[DownloadJob] = []
        self.active_runners: Dict[str, YtDlpRunner] = {}
        self.active_thumbnail_generators: Dict[str, ThumbnailGenerator] = {}
        
        self.queue_check_timer = QTimer(self)
        self.queue_check_timer.timeout.connect(self.start_next_jobs_in_queue)
        self.queue_check_timer.start(1000)

    def add_job(self, job: DownloadJob) -> None:
        logger.info(f"Lägger till jobb {job.id} ({job.url}) i kön.")
        self.queue.append(job)
        self.queue_changed.emit()
        self.save_jobs()

    def start_next_jobs_in_queue(self) -> None:
        max_concurrent = self.config_manager.get_config().max_parallel_downloads
        while len(self.active_runners) < max_concurrent:
            next_job = self._get_next_waiting_job()
            if next_job: self._start_job(next_job)
            else: break

    def _get_next_waiting_job(self) -> DownloadJob | None:
        return next((job for job in self.queue if job.status == JobStatus.STATUS_WAITING), None)

    def _start_job(self, job: DownloadJob) -> None:
        yt_dlp_path = self.config_manager.get_config().yt_dlp_path
        if not yt_dlp_path:
            logger.error("Kan inte starta jobb, sökväg till yt-dlp saknas.")
            job.status = JobStatus.STATUS_ERROR_STARTFAIL
            job.log += "Fel: Sökväg till yt-dlp är inte konfigurerad.\n"
            self._move_job_to_history(job)
            return
        logger.info(f"Försöker starta jobb {job.id}.")
        job.status = JobStatus.STATUS_STARTING
        self.job_updated.emit(job.id)
        runner = YtDlpRunner(job, yt_dlp_path)
        runner.process_started.connect(self._on_process_started)
        runner.process_finished.connect(self._on_process_finished)
        runner.output_received.connect(self._on_output_received)
        runner.error_occurred.connect(self._on_process_error)
        self.active_runners[job.id] = runner
        self.active_jobs_count_changed.emit(len(self.active_runners))
        runner.start()

    def cancel_job(self, job_id: str) -> None:
        if job_id in self.active_runners:
            logger.info(f"Avbryter aktivt jobb {job_id}.")
            job = self.active_runners[job_id].job
            job.status = JobStatus.STATUS_CANCELLING
            self.job_updated.emit(job.id)
            self.active_runners[job_id].cancel()
        else:
            job = self.get_job_from_queue(job_id)
            if job and job.status == JobStatus.STATUS_WAITING:
                logger.info(f"Avbryter väntande jobb {job_id}.")
                job.status = JobStatus.STATUS_CANCELLED
                self._move_job_to_history(job)

    def _move_job_to_history(self, job: DownloadJob) -> None:
        if job in self.queue:
            self.queue.remove(job)
            self.history.insert(0, job)
            self.queue_changed.emit()
            self.history_changed.emit()
            self.save_jobs()
            logger.info(f"Jobb {job.id} flyttat till historik med status {job.status.name}.")

    def _on_process_started(self, job_id: str) -> None:
        job = self.active_runners[job_id].job
        job.status = JobStatus.STATUS_RUNNING
        self.job_updated.emit(job_id)

    def _on_output_received(self, job_id: str, output: str) -> None:
        if job_id not in self.active_runners: return
        job = self.active_runners[job_id].job
        job.log += output
        
        progress_match = re.search(r'\[download\]\s+([\d.]+)%', output)
        if progress_match: job.progress = float(progress_match.group(1))
        
        final_file_match = (
            re.search(r'\[Merger\] Merging formats into "(.*)"', output) or
            re.search(r'\[ExtractAudio\] Destination: (.*)', output) or
            re.search(r'\[download\] Destination: (.*)', output)
        )
        if final_file_match:
            job.final_filename = os.path.basename(final_file_match.group(1).strip())
        
        thumb_match = re.search(r'Writing thumbnail to: (.*)', output)
        if thumb_match:
            thumb_path = thumb_match.group(1).strip()
            if not os.path.isabs(thumb_path) and job.output_path:
                job.thumbnail_path = os.path.join(job.output_path, thumb_path)
            else:
                job.thumbnail_path = thumb_path
            logger.info(f"Hittade miniatyrbild för jobb {job.id}: {job.thumbnail_path}")

        # **FIX:** Mer robust logik för att hitta videolängd.
        if not job.duration:
            duration_match = re.search(r'Duration:\s*([\d:.]+)', output)
            if duration_match:
                job.duration = duration_match.group(1).strip().split('.')[0] # Ta bort millisekunder
                logger.info(f"Hittade längd för jobb {job.id}: {job.duration}")

        if job.title == "N/A" and job.final_filename:
            job.title = os.path.splitext(job.final_filename)[0]

        self.job_updated.emit(job.id)

    def _on_process_finished(self, job_id: str, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if job_id not in self.active_runners:
            logger.warning(f"Fick 'finished' signal för okänt jobb: {job_id}")
            return
        runner = self.active_runners.pop(job_id)
        self.active_jobs_count_changed.emit(len(self.active_runners))
        job = runner.job
        if job.status == JobStatus.STATUS_CANCELLING:
            job.status = JobStatus.STATUS_CANCELLED
        elif exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            job.status = JobStatus.STATUS_COMPLETED
            job.progress = 100.0
        else:
            job.status = JobStatus.STATUS_ERROR_PROCESS
            if "already been downloaded" in job.log:
                job.status = JobStatus.STATUS_ALREADY_DOWNLOADED
            elif exit_status == QProcess.ExitStatus.CrashExit:
                job.status = JobStatus.STATUS_ERROR_CRASH
        
        self._move_job_to_history(job)
        self._generate_thumbnail_if_needed(job)
        self.start_next_jobs_in_queue()

    def _generate_thumbnail_if_needed(self, job: DownloadJob):
        if job.status in (JobStatus.STATUS_COMPLETED, JobStatus.STATUS_ALREADY_DOWNLOADED) and not job.thumbnail_path:
            ffmpeg_path = self.config_manager.get_config().ffmpeg_path
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                logger.info(f"Ingen miniatyrbild hittades för jobb {job.id}, försöker generera med FFmpeg.")
                generator = ThumbnailGenerator(job, ffmpeg_path)
                generator.thumbnail_generated.connect(self._on_thumbnail_generated)
                generator.generation_failed.connect(self._on_thumbnail_failed)
                self.active_thumbnail_generators[job.id] = generator
                generator.generate()
            else:
                logger.warning(f"Kan inte generera miniatyrbild för jobb {job.id}: FFmpeg-sökväg saknas eller är ogiltig.")

    def trigger_thumbnail_generation(self, job_id: str):
        job = self.get_job_from_history(job_id)
        if job:
            self._generate_thumbnail_if_needed(job)
        else:
            logger.warning(f"Kunde inte trigga thumbnail-generering för obefintligt jobb {job_id}")

    def _on_thumbnail_generated(self, job_id: str, thumbnail_path: str):
        job = self.get_job_from_history(job_id)
        if job:
            job.thumbnail_path = thumbnail_path
            self.job_updated.emit(job_id)
            self.save_jobs()
        self.active_thumbnail_generators.pop(job_id, None)

    def _on_thumbnail_failed(self, job_id: str):
        logger.warning(f"Misslyckades med att generera miniatyrbild för jobb {job_id}.")
        self.active_thumbnail_generators.pop(job_id, None)

    def _on_process_error(self, job_id: str, error: QProcess.ProcessError) -> None:
        if job_id not in self.active_runners: return
        runner = self.active_runners.pop(job_id)
        self.active_jobs_count_changed.emit(len(self.active_runners))
        job = runner.job
        job.status = JobStatus.STATUS_ERROR_STARTFAIL
        job.log += f"Processfel: {error.name} - {runner.process.errorString()}\n"
        self._move_job_to_history(job)
        self.start_next_jobs_in_queue()

    def retry_job(self, job_id: str) -> None:
        job_to_retry = self.get_job_from_history(job_id)
        if job_to_retry:
            logger.info(f"Försöker jobb {job_id} igen.")
            job_to_retry.status = JobStatus.STATUS_WAITING
            job_to_retry.progress = 0.0
            job_to_retry.log = ""
            job_to_retry.added_time = datetime.now().isoformat()
            job_to_retry.thumbnail_path = None
            self.history.remove(job_to_retry)
            self.queue.append(job_to_retry)
            self.history_changed.emit()
            self.queue_changed.emit()
            self.save_jobs()
            self.start_next_jobs_in_queue()

    def get_job_from_queue(self, job_id: str) -> DownloadJob | None:
        return next((j for j in self.queue if j.id == job_id), None)
        
    def get_job_from_history(self, job_id: str) -> DownloadJob | None:
        return next((j for j in self.history if j.id == job_id), None)

    def clear_history(self) -> None:
        self.history.clear()
        self.history_changed.emit()
        self.save_jobs()

    def remove_job(self, job_id: str) -> None:
        job_q = self.get_job_from_queue(job_id)
        if job_q and job_q.status == JobStatus.STATUS_WAITING:
            self.queue.remove(job_q)
            self.queue_changed.emit()
            self.save_jobs()
        else:
            job_h = self.get_job_from_history(job_id)
            if job_h:
                self.history.remove(job_h)
                self.history_changed.emit()
                self.save_jobs()
    
    def get_jobs_path(self, filename: str = "jobs.json") -> str:
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        return f"{app_data_path}/{filename}"

    def save_jobs(self) -> None:
        if not self.config_manager.get_config().save_queue_on_exit: return
        self.export_jobs(self.get_jobs_path())

    def load_jobs(self) -> None:
        try:
            self.import_jobs(self.get_jobs_path())
            for job in self.queue:
                if job.status not in [JobStatus.STATUS_COMPLETED, JobStatus.STATUS_CANCELLED] and not job.status.name.startswith("STATUS_ERROR"):
                     job.status = JobStatus.STATUS_WAITING
                     job.progress = 0.0
            self.queue_changed.emit()
            self.history_changed.emit()
            self.start_next_jobs_in_queue()
        except FileNotFoundError:
            logger.info("Jobb-filen hittades inte, startar med tom kö/historik.")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Fel vid laddning av jobb: {e}")

    def export_jobs(self, file_path: str) -> None:
        data = {"queue": [job.to_dict() for job in self.queue], "history": [job.to_dict() for job in self.history]}
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Kö och historik exporterad till {file_path}.")
        except IOError as e:
            logger.error(f"Kunde inte exportera jobb till {file_path}: {e}")

    def import_jobs(self, file_path: str) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.queue = [DownloadJob.from_dict(d) for d in data.get("queue", [])]
            self.history = [DownloadJob.from_dict(d) for d in data.get("history", [])]
            logger.info(f"Importerade {len(self.queue)} jobb till kön och {len(self.history)} till historiken från {file_path}.")
        self.queue_changed.emit()
        self.history_changed.emit()
        self.start_next_jobs_in_queue()
