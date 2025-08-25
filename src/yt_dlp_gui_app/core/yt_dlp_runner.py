import logging
from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from yt_dlp_gui_app.core.models import DownloadJob, JobStatus

logger = logging.getLogger(__name__)

class YtDlpRunner(QObject):
    """
    En wrapper runt QProcess för att köra yt-dlp-kommandon asynkront.
    Hanterar en enskild nedladdningsprocess.
    """
    # Signaler för att kommunicera med JobManager
    process_started = pyqtSignal(str)  # job_id
    process_finished = pyqtSignal(str, int, QProcess.ExitStatus)  # job_id, exit_code, exit_status
    output_received = pyqtSignal(str, str)  # job_id, output_data
    error_occurred = pyqtSignal(str, QProcess.ProcessError) # job_id, error

    def __init__(self, job: DownloadJob, yt_dlp_path: str, parent: QObject | None = None):
        super().__init__(parent)
        self.job = job
        self.yt_dlp_path = yt_dlp_path
        self.process = QProcess()
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Ansluter QProcess-signaler till klassens metoder."""
        self.process.readyReadStandardOutput.connect(self._on_ready_read_stdout)
        self.process.readyReadStandardError.connect(self._on_ready_read_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)
        self.process.started.connect(self._on_started)

    def start(self) -> None:
        """Startar yt-dlp-processen med jobbets argument."""
        if not self.yt_dlp_path:
            logger.error(f"yt-dlp sökväg är inte satt för jobb {self.job.id}")
            self.job.status = JobStatus.STATUS_ERROR_STARTFAIL
            self.job.log += "Fel: Sökväg till yt-dlp är inte konfigurerad.\n"
            # Manuell emit eftersom processen aldrig startar
            self.process_finished.emit(self.job.id, -1, QProcess.ExitStatus.CrashExit)
            return

        command = self.yt_dlp_path
        args = self.job.args_list + [self.job.url]
        
        logger.info(f"Startar process för jobb {self.job.id}: '{command}' med argument {args}")
        self.job.log += f"Kommando: {command} {' '.join(args)}\n\n"
        
        if self.job.output_path:
            self.process.setWorkingDirectory(self.job.output_path)

        self.process.start(command, args)

    def cancel(self) -> None:
        """Avbryter den körande processen."""
        if self.process.state() == QProcess.ProcessState.Running:
            logger.info(f"Avbryter process för jobb {self.job.id}")
            self.process.kill() # Använd kill för att säkerställa att processen avslutas

    def _on_started(self) -> None:
        """Hanterar när processen har startat."""
        logger.info(f"Process startad för jobb {self.job.id} med PID {self.process.processId()}")
        self.process_started.emit(self.job.id)

    def _on_ready_read_stdout(self) -> None:
        """Läser data från stdout."""
        output = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.output_received.emit(self.job.id, output)

    def _on_ready_read_stderr(self) -> None:
        """Läser data från stderr."""
        error_output = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.output_received.emit(self.job.id, error_output)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        """Hanterar när processen har avslutats."""
        logger.info(f"Process för jobb {self.job.id} avslutad. Kod: {exit_code}, Status: {exit_status.name}")
        # Läs eventuell kvarvarande output
        remaining_output = self.process.readAll().data().decode('utf-8', errors='ignore')
        if remaining_output:
            self.output_received.emit(self.job.id, remaining_output)
            
        self.process_finished.emit(self.job.id, exit_code, exit_status)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        """Hanterar processfel."""
        error_string = self.process.errorString()
        logger.error(f"Processfel för jobb {self.job.id}: {error.name} - {error_string}")
        self.error_occurred.emit(self.job.id, error)

