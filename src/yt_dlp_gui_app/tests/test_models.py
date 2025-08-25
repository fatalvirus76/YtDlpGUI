from yt_dlp_gui_app.core.models import DownloadJob, JobStatus

def test_download_job_creation():
    """Testar att ett DownloadJob-objekt skapas med korrekta standardvärden."""
    job = DownloadJob(url="http://example.com")
    assert job.url == "http://example.com"
    assert job.status == JobStatus.STATUS_WAITING
    assert job.progress == 0.0
    assert isinstance(job.id, str)
    assert job.title == "N/A"

def test_job_serialization_deserialization():
    """Testar att serialisering till dict och tillbaka fungerar korrekt."""
    job = DownloadJob(
        url="http://example.com",
        title="Test Video",
        status=JobStatus.STATUS_RUNNING,
        progress=50.5,
        output_path="/tmp"
    )
    job_dict = job.to_dict()

    assert job_dict["url"] == "http://example.com"
    assert job_dict["status"] == "STATUS_RUNNING"
    assert job_dict["progress"] == 50.5

    rehydrated_job = DownloadJob.from_dict(job_dict)
    assert rehydrated_job.url == job.url
    assert rehydrated_job.status == job.status
    assert rehydrated_job.progress == job.progress
    assert rehydrated_job.id == job.id

def test_job_deserialization_with_missing_keys():
    """Testar att deserialisering hanterar saknade nycklar med standardvärden."""
    job_dict = {"url": "http://test.com"}
    job = DownloadJob.from_dict(job_dict)
    assert job.url == "http://test.com"
    assert job.status == JobStatus.STATUS_WAITING
    assert job.title == "N/A"

def test_job_deserialization_with_invalid_status():
    """Testar att en ogiltig statussträng återgår till standardvärdet."""
    job_dict = {"url": "http://test.com", "status": "INVALID_STATUS"}
    job = DownloadJob.from_dict(job_dict)
    assert job.status == JobStatus.STATUS_WAITING

