import sys
import logging
from PyQt6.QtWidgets import QApplication
from yt_dlp_gui_app.ui.main_window import MainWindow
from yt_dlp_gui_app.core.config import ConfigManager
from yt_dlp_gui_app.core.job_manager import JobManager
from yt_dlp_gui_app.core.ui_bridge import UIBridge

# --- Grundläggande loggningskonfiguration ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Applikationens huvudfunktion.
    Initialiserar QApplication, kärnkomponenter och huvudfönstret.
    """
    logger.info("Applikationen startar...")

    app = QApplication(sys.argv)
    app.setOrganizationName("YtDlpGUI")
    app.setApplicationName("YtDlpGUI")

    # --- Initialisera kärnkomponenter ---
    config_manager = ConfigManager()
    config_manager.load_config()

    job_manager = JobManager(config_manager)
    
    ui_bridge = UIBridge(job_manager, config_manager)

    # --- Initialisera huvudfönstret ---
    window = MainWindow(ui_bridge, config_manager)
    window.show()

    logger.info("Huvudfönstret har visats. Startar event-loopen.")
    
    # Ladda jobb efter att fönstret har skapats för att säkerställa att signaler är anslutna
    job_manager.load_jobs()

    try:
        sys.exit(app.exec())
    except SystemExit:
        logger.info("Applikationen stängs ner.")
    except Exception as e:
        logger.critical(f"Ohanterat undantag i event-loopen: {e}", exc_info=True)

if __name__ == '__main__':
    main()

