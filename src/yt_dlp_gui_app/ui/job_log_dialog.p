from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
from yt_dlp_gui_app.core.models import DownloadJob

class JobLogDialog(QDialog):
    """En enkel dialog för att visa den fullständiga loggen för ett jobb."""

    def __init__(self, job: DownloadJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.setWindowTitle(f"Logg för: {job.title}")
        self.setGeometry(200, 200, 800, 600)

        self.layout = QVBoxLayout(self)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setText(job.log)
        self.log_view.setFontFamily("monospace")
        self.layout.addWidget(self.log_view)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)
        self.layout.addWidget(self.button_box)

