import shlex
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, 
    QFileDialog, QSpinBox, QComboBox, QDialogButtonBox, QHBoxLayout,
    QTabWidget, QWidget, QCheckBox
)
from yt_dlp_gui_app.core.config import ConfigManager

class SettingsDialog(QDialog):
    """En dialog för att ändra applikationens inställningar."""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Inställningar")
        self.setMinimumWidth(600)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self._create_general_tab()
        self._create_download_options_tab()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self._load_settings()
        self._connect_signals()

    def _create_general_tab(self):
        self.general_tab = QWidget()
        layout = QFormLayout(self.general_tab)

        # Sökvägar
        self.yt_dlp_path_edit = QLineEdit()
        yt_dlp_browse_button = QPushButton("Bläddra...")
        yt_dlp_browse_button.clicked.connect(lambda: self._browse_for_executable(self.yt_dlp_path_edit, "Välj yt-dlp"))
        path_layout_yt = QHBoxLayout()
        path_layout_yt.addWidget(self.yt_dlp_path_edit)
        path_layout_yt.addWidget(yt_dlp_browse_button)
        layout.addRow("Sökväg till yt-dlp:", path_layout_yt)
        
        self.ffmpeg_path_edit = QLineEdit() # NYTT FÄLT
        ffmpeg_browse_button = QPushButton("Bläddra...")
        ffmpeg_browse_button.clicked.connect(lambda: self._browse_for_executable(self.ffmpeg_path_edit, "Välj ffmpeg"))
        path_layout_ffmpeg = QHBoxLayout()
        path_layout_ffmpeg.addWidget(self.ffmpeg_path_edit)
        path_layout_ffmpeg.addWidget(ffmpeg_browse_button)
        layout.addRow("Sökväg till ffmpeg:", path_layout_ffmpeg)

        self.default_args_edit = QLineEdit()
        self.default_args_edit.setPlaceholderText("--ignore-errors (för avancerade användare)")
        layout.addRow("Extra standardargument:", self.default_args_edit)

        self.max_downloads_spinbox = QSpinBox()
        self.max_downloads_spinbox.setMinimum(1)
        self.max_downloads_spinbox.setMaximum(20)
        layout.addRow("Max parallella nedladdningar:", self.max_downloads_spinbox)

        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["default", "dark", "synthwave", "matrix", "dracula"])
        layout.addRow("Tema:", self.theme_combobox)

        self.tabs.addTab(self.general_tab, "Allmänt")

    def _create_download_options_tab(self):
        self.download_tab = QWidget()
        layout = QFormLayout(self.download_tab)
        self.format_edit = QLineEdit()
        layout.addRow("Videoformat (-f):", self.format_edit)
        self.extract_audio_check = QCheckBox("Extrahera endast ljud (-x)")
        layout.addRow(self.extract_audio_check)
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["best", "mp3", "aac", "m4a", "flac", "wav", "opus"])
        layout.addRow("Ljudformat:", self.audio_format_combo)
        self.write_thumbnail_check = QCheckBox("Ladda ner miniatyrbild (separat fil)")
        self.embed_thumbnail_check = QCheckBox("Bädda in miniatyrbild (i videofilen)")
        layout.addRow(self.write_thumbnail_check)
        layout.addRow(self.embed_thumbnail_check)
        self.write_subs_check = QCheckBox("Ladda ner undertexter")
        layout.addRow(self.write_subs_check)
        self.sub_langs_edit = QLineEdit()
        layout.addRow("Undertextspråk:", self.sub_langs_edit)
        self.tabs.addTab(self.download_tab, "Nedladdningsalternativ")

    def _connect_signals(self):
        self.extract_audio_check.toggled.connect(self.audio_format_combo.setEnabled)
        self.write_subs_check.toggled.connect(self.sub_langs_edit.setEnabled)

    def _browse_for_executable(self, line_edit: QLineEdit, title: str):
        file_path, _ = QFileDialog.getOpenFileName(self, title)
        if file_path:
            line_edit.setText(file_path)

    def _load_settings(self):
        config = self.config_manager.get_config()
        self.yt_dlp_path_edit.setText(config.yt_dlp_path or "")
        self.ffmpeg_path_edit.setText(config.ffmpeg_path or "") # NY RAD
        self.default_args_edit.setText(shlex.join(config.default_args))
        self.max_downloads_spinbox.setValue(config.max_parallel_downloads)
        self.theme_combobox.setCurrentText(config.theme)
        self.format_edit.setText(config.download_format)
        self.extract_audio_check.setChecked(config.extract_audio)
        self.audio_format_combo.setCurrentText(config.audio_format)
        self.audio_format_combo.setEnabled(config.extract_audio)
        self.write_thumbnail_check.setChecked(config.write_thumbnail)
        self.embed_thumbnail_check.setChecked(config.embed_thumbnail)
        self.write_subs_check.setChecked(config.write_subs)
        self.sub_langs_edit.setText(config.sub_langs)
        self.sub_langs_edit.setEnabled(config.write_subs)

    def accept(self):
        config = self.config_manager.get_config()
        config.yt_dlp_path = self.yt_dlp_path_edit.text()
        config.ffmpeg_path = self.ffmpeg_path_edit.text() # NY RAD
        config.default_args = shlex.split(self.default_args_edit.text())
        config.max_parallel_downloads = self.max_downloads_spinbox.value()
        config.theme = self.theme_combobox.currentText()
        config.download_format = self.format_edit.text()
        config.extract_audio = self.extract_audio_check.isChecked()
        config.audio_format = self.audio_format_combo.currentText()
        config.write_thumbnail = self.write_thumbnail_check.isChecked()
        config.embed_thumbnail = self.embed_thumbnail_check.isChecked()
        config.write_subs = self.write_subs_check.isChecked()
        config.sub_langs = self.sub_langs_edit.text()
        self.config_manager.save_config()
        super().accept()

