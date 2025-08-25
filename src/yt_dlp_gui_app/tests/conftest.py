import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Skapar en QApplication-instans för testerna."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

