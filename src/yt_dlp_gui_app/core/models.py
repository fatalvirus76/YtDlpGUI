import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional

class JobStatus(Enum):
    """Enumeration för status på ett nedladdningsjobb."""
    STATUS_WAITING = auto()
    STATUS_STARTING = auto()
    STATUS_RUNNING = auto()
    STATUS_COMPLETED = auto()
    STATUS_CANCELLED = auto()
    STATUS_CANCELLING = auto()
    STATUS_ERROR_STARTFAIL = auto()
    STATUS_ERROR_EXCEPTION = auto()
    STATUS_ERROR_CRASH = auto()
    STATUS_ERROR_PROCESS = auto()
    STATUS_ERROR_YTDLP = auto()
    STATUS_ALREADY_DOWNLOADED = auto()
    STATUS_MERGING = auto()
    STATUS_POSTPROCESSING = auto()

@dataclass
class DownloadJob:
    """
    Representerar ett enskilt nedladdningsjobb.
    Använder dataclass för att förenkla skapandet av datastrukturer.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    title: str = "N/A"
    args_list: List[str] = field(default_factory=list)
    status: JobStatus = JobStatus.STATUS_WAITING
    progress: float = 0.0
    added_time: str = field(default_factory=lambda: datetime.now().isoformat())
    output_path: Optional[str] = None
    final_filename: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration: Optional[str] = None # NYTT FÄLT
    log: str = ""

    def to_dict(self) -> dict:
        """Serialiserar objektet till en dictionary för JSON-lagring."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "args_list": self.args_list,
            "status": self.status.name,
            "progress": self.progress,
            "added_time": self.added_time,
            "output_path": self.output_path,
            "final_filename": self.final_filename,
            "thumbnail_path": self.thumbnail_path,
            "duration": self.duration, # NYTT FÄLT
            "log": self.log,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadJob":
        """Skapar ett DownloadJob-objekt från en dictionary."""
        status_name = data.get("status", "STATUS_WAITING")
        try:
            status = JobStatus[status_name]
        except KeyError:
            status = JobStatus.STATUS_WAITING
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            url=data.get("url", ""),
            title=data.get("title", "N/A"),
            args_list=data.get("args_list", []),
            status=status,
            progress=data.get("progress", 0.0),
            added_time=data.get("added_time", datetime.now().isoformat()),
            output_path=data.get("output_path"),
            final_filename=data.get("final_filename"),
            thumbnail_path=data.get("thumbnail_path"),
            duration=data.get("duration"), # NYTT FÄLT
            log=data.get("log", ""),
        )
