import pytest
from unittest.mock import MagicMock, patch
from yt_dlp_gui_app.core.job_manager import JobManager
from yt_dlp_gui_app.core.models import DownloadJob, JobStatus

@pytest.fixture
def mock_config_manager():
    """Skapar en mock för ConfigManager."""
    manager = MagicMock()
    manager.get_config.return_value.yt_dlp_path = "/fake/yt-dlp"
    manager.get_config.return_value.max_parallel_downloads = 2
    return manager

@pytest.fixture
def job_manager(mock_config_manager, qapp):
    """Skapar en JobManager-instans för testning."""
    return JobManager(config_manager=mock_config_manager)

def test_add_job(job_manager: JobManager):
    """Testar att lägga till ett jobb i kön."""
    job = DownloadJob(url="url1")
    job_manager.add_job(job)
    assert len(job_manager.queue) == 1
    assert job_manager.queue[0] == job

@patch('yt_dlp_gui_app.core.job_manager.YtDlpRunner')
def test_start_next_jobs_in_queue(MockYtDlpRunner, job_manager: JobManager):
    """Testar att jobb startas från kön enligt max_parallel_downloads."""
    job1 = DownloadJob(url="url1")
    job2 = DownloadJob(url="url2")
    job3 = DownloadJob(url="url3")
    
    job_manager.add_job(job1)
    job_manager.add_job(job2)
    job_manager.add_job(job3)
    
    job_manager.start_next_jobs_in_queue()
    
    # Två jobb ska ha startats
    assert MockYtDlpRunner.call_count == 2
    assert len(job_manager.active_runners) == 2
    assert job1.status == JobStatus.STATUS_STARTING
    assert job2.status == JobStatus.STATUS_STARTING
    assert job3.status == JobStatus.STATUS_WAITING

def test_start_job_no_yt_dlp_path(job_manager: JobManager, mock_config_manager):
    """Testar att ett jobb misslyckas korrekt om yt-dlp-sökvägen saknas."""
    mock_config_manager.get_config.return_value.yt_dlp_path = None
    job = DownloadJob(url="url1")
    job_manager.add_job(job)
    
    job_manager.start_next_jobs_in_queue()
    
    assert len(job_manager.active_runners) == 0
    assert len(job_manager.queue) == 0
    assert len(job_manager.history) == 1
    assert job_manager.history[0].status == JobStatus.STATUS_ERROR_STARTFAIL

def test_move_job_to_history(job_manager: JobManager):
    """Testar att ett jobb flyttas korrekt från kön till historiken."""
    job = DownloadJob(url="url1")
    job_manager.add_job(job)
    
    job.status = JobStatus.STATUS_COMPLETED
    job_manager._move_job_to_history(job)
    
    assert len(job_manager.queue) == 0
    assert len(job_manager.history) == 1
    assert job_manager.history[0] == job

