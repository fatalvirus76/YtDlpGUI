import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QProcess
from yt_dlp_gui_app.core.yt_dlp_runner import YtDlpRunner
from yt_dlp_gui_app.core.models import DownloadJob, JobStatus

@pytest.fixture
def job():
    return DownloadJob(url="http://example.com", args_list=["-f", "best"])

@pytest.fixture
def runner(job, qapp):
    return YtDlpRunner(job=job, yt_dlp_path="/fake/yt-dlp")

@patch('PyQt6.QtCore.QProcess.start')
def test_start_process(mock_start, runner: YtDlpRunner):
    """Testar att QProcess.start anropas med rätt argument."""
    runner.start()
    mock_start.assert_called_once_with("/fake/yt-dlp", ["-f", "best", "http://example.com"])

def test_start_process_no_path(runner: YtDlpRunner):
    """Testar att start misslyckas om sökvägen till yt-dlp saknas."""
    runner.yt_dlp_path = ""
    # Använd en mock för att fånga den utsända signalen
    mock_slot = MagicMock()
    runner.process_finished.connect(mock_slot)
    
    runner.start()
    
    assert runner.job.status == JobStatus.STATUS_ERROR_STARTFAIL
    mock_slot.assert_called_once_with(runner.job.id, -1, QProcess.ExitStatus.CrashExit)

@patch('PyQt6.QtCore.QProcess.kill')
def test_cancel_process(mock_kill, runner: YtDlpRunner):
    """Testar att QProcess.kill anropas när man avbryter."""
    # Få processen att se ut som att den körs
    with patch.object(runner.process, 'state', return_value=QProcess.ProcessState.Running):
        runner.cancel()
        mock_kill.assert_called_once()

