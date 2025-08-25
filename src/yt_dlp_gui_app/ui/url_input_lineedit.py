from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class UrlInputLineEdit(QLineEdit):
    """
    En anpassad QLineEdit som accepterar drag-and-drop av filer.
    Läser innehållet i textfiler och lägger till det i fältet.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accepterar eventet om det innehåller URL:er (filer)."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Hanterar när en fil släpps på widgeten."""
        if event.mimeData().hasUrls():
            urls_content = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    try:
                        # Försök att läsa filen som en textfil
                        with open(file_path, 'r', encoding='utf-8') as f:
                            urls_content.append(f.read())
                    except Exception as e:
                        self.setText(f"Kunde inte läsa filen: {e}")
            
            if urls_content:
                # Sammanfoga innehållet från alla filer, separerat med mellanslag
                full_text = " ".join(urls_content).replace('\n', ' ').strip()
                self.setText(full_text)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

