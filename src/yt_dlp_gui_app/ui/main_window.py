import logging
import os
from PyQt6.QtCore import Qt, QModelIndex, QUrl
from PyQt6.QtGui import QAction, QColor, QStandardItemModel, QStandardItem, QDesktopServices, QClipboard, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QTableView,
    QHeaderView, QLineEdit, QPushButton, QHBoxLayout, QProgressBar,
    QFileDialog, QMessageBox, QTextEdit, QMenu, QLabel, QStatusBar
)
from yt_dlp_gui_app.core.config import ConfigManager
from yt_dlp_gui_app.core.models import DownloadJob, JobStatus
from yt_dlp_gui_app.core.ui_bridge import UIBridge
from yt_dlp_gui_app.ui.settings_dialog import SettingsDialog
from yt_dlp_gui_app.ui.theme_manager import ThemeManager
from yt_dlp_gui_app.ui.url_input_lineedit import UrlInputLineEdit

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Applikationens huvudfönster."""

    def __init__(self, ui_bridge: UIBridge, config_manager: ConfigManager):
        super().__init__()
        self.ui_bridge = ui_bridge
        self.config_manager = config_manager
        self.theme_manager = ThemeManager()
        self.last_clipboard_url = ""

        self.setWindowTitle("YtDlpGUI")
        self.setGeometry(100, 100, 1200, 800)

        self._init_ui()
        self._init_status_bar()
        self._connect_signals()
        self._setup_clipboard_listener()
        self._update_theme()
        
        self.check_executables_path()
        self.update_queue_view()
        self.update_history_view()

    def _init_ui(self) -> None:
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        url_layout = QHBoxLayout()
        self.url_input = UrlInputLineEdit()
        self.url_input.setPlaceholderText("Klistra in URL(er) här...")
        self.add_button = QPushButton("Lägg till i kön")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.add_button)
        self.layout.addLayout(url_layout)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Spara till:"))
        self.path_input = QLineEdit()
        self.path_input.setText(self.config_manager.get_config().last_output_dir)
        self.browse_path_button = QPushButton("Bläddra...")
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_path_button)
        self.layout.addLayout(path_layout)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.queue_tab = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_tab)
        self.queue_table = self._create_table_view()
        self.queue_model = self._create_table_model(is_history=False)
        self.queue_table.setModel(self.queue_model)
        self._setup_table_columns(self.queue_table, is_history=False)
        self.queue_layout.addWidget(self.queue_table)
        self.tabs.addTab(self.queue_tab, "Kö")
        self.history_tab = QWidget()
        self.history_layout = QVBoxLayout(self.history_tab)
        self.generate_thumbs_button = QPushButton("Generera valda miniatyrbilder")
        self.history_layout.addWidget(self.generate_thumbs_button)
        self.history_table = self._create_table_view()
        self.history_model = self._create_table_model(is_history=True)
        self.history_table.setModel(self.history_model)
        self._setup_table_columns(self.history_table, is_history=True)
        self.history_layout.addWidget(self.history_table)
        self.tabs.addTab(self.history_tab, "Historik")
        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout(self.log_tab)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_layout.addWidget(self.log_view)
        self.tabs.addTab(self.log_tab, "Logg")
        self._create_menu()

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.active_label = QLabel("Aktiva: 0")
        self.queue_label = QLabel("I kö: 0")
        self.history_label = QLabel("Historik: 0")
        self.status_bar.addPermanentWidget(self.active_label)
        self.status_bar.addPermanentWidget(self.queue_label)
        self.status_bar.addPermanentWidget(self.history_label)

    def _create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Arkiv")
        save_action = QAction("Spara kö...", self)
        save_action.triggered.connect(self._on_save_queue)
        load_action = QAction("Ladda kö...", self)
        load_action.triggered.connect(self._on_load_queue)
        exit_action = QAction("Avsluta", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        tools_menu = menu_bar.addMenu("Verktyg")
        self.settings_action = QAction("Inställningar", self)
        tools_menu.addAction(self.settings_action)

    def _create_table_view(self) -> QTableView:
        table = QTableView()
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        return table

    def _create_table_model(self, is_history: bool = False) -> QStandardItemModel:
        headers = ["ID", "Titel", "Längd", "URL", "Status", "Framsteg", "Tillagd"]
        if is_history:
            headers.insert(1, "Miniatyr")
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(headers)
        return model

    def _setup_table_columns(self, table: QTableView, is_history: bool = False) -> None:
        header = table.horizontalHeader()
        model = table.model() # Hämta modellen från tabellen
        
        # Mappning av kolumnnamn till index
        idx_map = {model.headerData(i, Qt.Orientation.Horizontal): i for i in range(model.columnCount())}

        header.setSectionResizeMode(idx_map['Titel'], QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(idx_map['URL'], QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(idx_map['Status'], QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(idx_map['Längd'], QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(idx_map['Framsteg'], QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(idx_map['Tillagd'], QHeaderView.ResizeMode.ResizeToContents)
        
        if is_history:
            header.setSectionResizeMode(idx_map['Miniatyr'], QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(idx_map['Miniatyr'], 128)
            table.verticalHeader().setDefaultSectionSize(72)
        
        table.setColumnHidden(idx_map['ID'], True)
        table.setColumnWidth(idx_map['Framsteg'], 120)

    def _connect_signals(self) -> None:
        self.add_button.clicked.connect(self._on_add_clicked)
        self.browse_path_button.clicked.connect(self._on_browse_path)
        self.settings_action.triggered.connect(self._open_settings_dialog)
        self.generate_thumbs_button.clicked.connect(self._on_generate_thumbnails_clicked)
        self.queue_table.customContextMenuRequested.connect(self._open_queue_context_menu)
        self.history_table.customContextMenuRequested.connect(self._open_history_context_menu)
        self.ui_bridge.queue_changed.connect(self.update_queue_view)
        self.ui_bridge.history_changed.connect(self.update_history_view)
        self.ui_bridge.job_updated.connect(self._on_job_updated)
        self.ui_bridge.config_changed.connect(self._on_config_changed)
        self.ui_bridge.log_message.connect(self._on_log_message)
        self.ui_bridge.active_jobs_count_changed.connect(self._update_active_count)

    def _setup_clipboard_listener(self) -> None:
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)
        logger.info("Klippbordslyssnare aktiverad.")

    def update_queue_view(self) -> None:
        queue = self.ui_bridge.get_queue()
        self.queue_model.removeRows(0, self.queue_model.rowCount())
        for job in queue:
            self._add_or_update_job_in_model(self.queue_model, self.queue_table, job)
        self.queue_label.setText(f"I kö: {len(queue)}")

    def update_history_view(self) -> None:
        history = self.ui_bridge.get_history()
        self.history_model.removeRows(0, self.history_model.rowCount())
        for job in history:
            self._add_or_update_job_in_model(self.history_model, self.history_table, job)
        self.history_label.setText(f"Historik: {len(history)}")
            
    def _on_job_updated(self, job_id: str) -> None:
        job = self.ui_bridge.get_job(job_id)
        if job:
            if self._find_row_by_job_id(self.queue_model, job_id) is not None:
                self._add_or_update_job_in_model(self.queue_model, self.queue_table, job)
            elif self._find_row_by_job_id(self.history_model, job_id) is not None:
                 self._add_or_update_job_in_model(self.history_model, self.history_table, job)

    def _add_or_update_job_in_model(self, model: QStandardItemModel, table: QTableView, job: DownloadJob) -> None:
        row_index = self._find_row_by_job_id(model, job.id)
        is_history = "Miniatyr" in [model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]
        
        items = [
            QStandardItem(job.id), QStandardItem(job.title), QStandardItem(job.duration or ""),
            QStandardItem(job.url), QStandardItem(job.status.name.replace("STATUS_", "").replace("_", " ").title()),
            QStandardItem(), QStandardItem(job.added_time.split('.')[0].replace('T', ' '))
        ]
        if is_history:
            thumb_item = QStandardItem()
            if job.thumbnail_path and os.path.exists(job.thumbnail_path):
                pixmap = QPixmap(job.thumbnail_path)
                if not pixmap.isNull():
                    thumb_item.setData(pixmap.scaled(128, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation), Qt.ItemDataRole.DecorationRole)
            items.insert(1, thumb_item)
        
        status_color = self._get_status_color(job.status)
        if status_color:
            text_color = QColor("#000000")
            for item in items:
                item.setBackground(status_color)
                if not item.data(Qt.ItemDataRole.DecorationRole):
                     item.setForeground(text_color)
        
        if row_index is None:
            model.appendRow(items)
            row_index = model.rowCount() - 1
        else:
            for col, item in enumerate(items): model.setItem(row_index, col, item)
        
        progress_col_idx = 6 if is_history else 5
        progress_bar = QProgressBar()
        progress_bar.setValue(int(job.progress))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{job.progress:.1f}%")
        if status_color: progress_bar.setStyleSheet("color: #000000; text-align: center;")
        else: progress_bar.setStyleSheet("text-align: center;")
        if job.status == JobStatus.STATUS_RUNNING:
            table.setIndexWidget(model.index(row_index, progress_col_idx), progress_bar)
        else:
            progress_item = model.item(row_index, progress_col_idx)
            if progress_item: progress_item.setText(f"{job.progress:.1f}%")
            table.setIndexWidget(model.index(row_index, progress_col_idx), None)

    def _find_row_by_job_id(self, model: QStandardItemModel, job_id: str) -> int | None:
        for row in range(model.rowCount()):
            if model.item(row, 0).text() == job_id: return row
        return None

    def _get_status_color(self, status: JobStatus) -> QColor | None:
        if status in (JobStatus.STATUS_COMPLETED, JobStatus.STATUS_ALREADY_DOWNLOADED): return QColor("#d4edda")
        if status.name.startswith("STATUS_ERROR"): return QColor("#f8d7da")
        if status == JobStatus.STATUS_RUNNING: return QColor("#cce5ff")
        if status == JobStatus.STATUS_CANCELLED: return QColor("#fff3cd")
        return None

    def _add_urls_to_queue(self, urls: str) -> None:
        if not urls: return
        output_dir = self.path_input.text()
        if not output_dir or not os.path.isdir(output_dir):
             QMessageBox.warning(self, "Ogiltig mapp", "Den angivna mappen att spara till existerar inte.")
             return
        self.config_manager.set_last_output_dir(output_dir)
        self.ui_bridge.add_new_download(urls, output_dir)
        
    def _on_add_clicked(self) -> None:
        self._add_urls_to_queue(self.url_input.text())
        self.url_input.clear()

    def _on_browse_path(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Välj mapp att spara till", self.path_input.text())
        if directory:
            self.path_input.setText(directory)
            self.config_manager.set_last_output_dir(directory)

    def _on_clipboard_changed(self) -> None:
        text = self.clipboard.text().strip()
        if text and text.startswith("http") and text != self.last_clipboard_url:
            self.last_clipboard_url = text
            reply = QMessageBox.question(self, "Klippbordet upptäckt", f"URL upptäckt:\n\n{text}\n\nLägg till i kön?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self._add_urls_to_queue(text)

    def _on_save_queue(self):
        filePath, _ = QFileDialog.getSaveFileName(self, "Spara kö", "", "JSON Filer (*.json)")
        if filePath:
            self.ui_bridge.save_queue_to_file(filePath)

    def _on_load_queue(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Ladda kö", "", "JSON Filer (*.json)")
        if filePath:
            self.ui_bridge.load_queue_from_file(filePath)

    def _on_generate_thumbnails_clicked(self):
        selected_indexes = self.history_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Inget valt", "Markera en eller flera rader i historiken för att generera miniatyrbilder.")
            return
        job_ids = [self.history_model.index(index.row(), 0).data() for index in selected_indexes]
        for job_id in job_ids:
            self.ui_bridge.trigger_thumbnail_generation(job_id)
        QMessageBox.information(self, "Startat", f"Har påbörjat generering av miniatyrbilder för {len(job_ids)} jobb.")

    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()

    def _on_config_changed(self) -> None:
        logger.info("Konfigurationen har ändrats, uppdaterar UI.")
        self.path_input.setText(self.config_manager.get_config().last_output_dir)
        self._update_theme()
        self.check_executables_path()

    def _update_active_count(self, count: int):
        self.active_label.setText(f"Aktiva: {count}")

    def _update_theme(self) -> None:
        self.setStyleSheet(self.theme_manager.get_stylesheet(self.config_manager.get_config().theme))

    def _on_log_message(self, level: str, message: str) -> None:
        color_map = {"WARNING": "orange", "ERROR": "red", "CRITICAL": "purple"}
        color = color_map.get(level)
        if color: self.log_view.append(f"<font color='{color}'>{message}</font>")
        else: self.log_view.append(message)

    def check_executables_path(self) -> None:
        config = self.config_manager.get_config()
        missing = []
        if not config.yt_dlp_path or not os.path.exists(config.yt_dlp_path):
            missing.append("yt-dlp")
        if not config.ffmpeg_path or not os.path.exists(config.ffmpeg_path):
            missing.append("ffmpeg")
        if missing:
            QMessageBox.warning(self, "Program saknas", f"Sökvägen till följande program saknas eller är ogiltig: {', '.join(missing)}.\nVissa funktioner kommer inte fungera.\nAnge korrekta sökvägar under Verktyg > Inställningar.")

    def _get_selected_job_id(self, table: QTableView) -> str | None:
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes: return table.model().index(selected_indexes[0].row(), 0).data()
        return None

    def _open_queue_context_menu(self, position) -> None:
        job_id = self._get_selected_job_id(self.queue_table)
        if not job_id: return
        menu = QMenu()
        cancel_action = menu.addAction("Avbryt")
        remove_action = menu.addAction("Ta bort")
        log_action = menu.addAction("Visa logg")
        action = menu.exec(self.queue_table.viewport().mapToGlobal(position))
        if action == cancel_action: self.ui_bridge.cancel_job(job_id)
        elif action == remove_action: self.ui_bridge.remove_job(job_id)
        elif action == log_action: self._show_job_log(job_id)

    def _open_history_context_menu(self, position) -> None:
        job_id = self._get_selected_job_id(self.history_table)
        if not job_id: return
        job = self.ui_bridge.get_job(job_id)
        if not job: return
        menu = QMenu()
        play_action = menu.addAction("Spela lokalt")
        full_path = os.path.join(job.output_path, job.final_filename) if job.output_path and job.final_filename else None
        if not (full_path and os.path.exists(full_path)):
            play_action.setEnabled(False)
        retry_action = menu.addAction("Försök igen")
        if not job.status.name.startswith("STATUS_ERROR"):
            retry_action.setEnabled(False)
        generate_thumb_action = menu.addAction("Generera miniatyrbild")
        if (job.thumbnail_path and os.path.exists(job.thumbnail_path)) or not play_action.isEnabled():
            generate_thumb_action.setEnabled(False)
        log_action = menu.addAction("Visa logg")
        open_folder_action = menu.addAction("Öppna mapp")
        remove_action = menu.addAction("Ta bort")
        menu.addSeparator()
        clear_action = menu.addAction("Rensa historik")
        action = menu.exec(self.history_table.viewport().mapToGlobal(position))
        if action == play_action and full_path: QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
        elif action == retry_action: self.ui_bridge.retry_job(job_id)
        elif action == generate_thumb_action: self.ui_bridge.trigger_thumbnail_generation(job_id)
        elif action == log_action: self._show_job_log(job_id)
        elif action == open_folder_action:
            if job.output_path and os.path.isdir(job.output_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(job.output_path))
        elif action == remove_action: self.ui_bridge.remove_job(job_id)
        elif action == clear_action: self.ui_bridge.clear_history()

    def _show_job_log(self, job_id: str) -> None:
        from yt_dlp_gui_app.ui.job_log_dialog import JobLogDialog
        job = self.ui_bridge.get_job(job_id)
        if job:
            dialog = JobLogDialog(job, self)
            dialog.exec()

    def closeEvent(self, event) -> None:
        logger.info("Stänger fönstret, sparar jobb...")
        self.ui_bridge.job_manager.save_jobs()
        event.accept()
