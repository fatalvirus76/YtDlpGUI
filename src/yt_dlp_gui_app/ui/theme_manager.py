class ThemeManager:
    """Hanterar stylesheets för olika teman."""

    def __init__(self):
        self.themes = {
            "default": self._get_default_stylesheet(),
            "dark": self._get_dark_stylesheet(),
            "synthwave": self._get_synthwave_stylesheet(),
            "matrix": self._get_matrix_stylesheet(),
            "dracula": self._get_dracula_stylesheet(),
        }

    def get_stylesheet(self, theme_name: str) -> str:
        """Returnerar stylesheet för ett givet tema."""
        return self.themes.get(theme_name, self.themes["default"])

    def _get_common_dark_elements(self, bg: str, text: str, base: str, highlight: str) -> str:
        """Gemensam CSS för mörka teman för att undvika repetition."""
        return f"""
            QMainWindow, QDialog {{
                background-color: {bg};
            }}
            QWidget {{
                background-color: {bg};
                color: {text};
                font-size: 10pt;
            }}
            QTabWidget::pane {{ border: 1px solid {base}; }}
            QTabBar::tab {{
                background: {base};
                color: {text};
                padding: 8px;
                border: 1px solid {base};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{ background: {highlight}; }}
            QTableView, QTextEdit {{
                background-color: {base};
                color: {text};
                gridline-color: {highlight};
                alternate-background-color: #3a3a3a;
            }}
            /* **FIX:** Regeln som tvingade all text att vara ljus är nu borttagen. */
            /* Färgen styrs nu korrekt från main_window.py för specifika rader. */
            QHeaderView::section {{
                background-color: {highlight};
                color: {text};
                padding: 4px;
                border: 1px solid {base};
            }}
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {base};
                color: {text};
                border: 1px solid {highlight};
                padding: 4px;
            }}
            QPushButton {{
                background-color: {highlight};
                color: {text};
                border: 1px solid {base};
                padding: 5px 15px;
            }}
            QPushButton:hover {{ background-color: {base}; }}
            QProgressBar {{
                border: 1px solid {base};
                text-align: center;
                /* Låt progressbaren ärva textfärgen för att fungera med både ljus och mörk text */
            }}
            QMenu {{
                background-color: {base};
                border: 1px solid {highlight};
            }}
            QMenu::item:selected {{
                background-color: {highlight};
            }}
        """

    def _get_default_stylesheet(self) -> str:
        """Returnerar en grundläggande, ljus stylesheet."""
        return """
            QWidget { font-size: 10pt; }
            QTableView { gridline-color: #d0d0d0; }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
            }
            QPushButton { padding: 5px 15px; }
        """

    def _get_dark_stylesheet(self) -> str:
        """Returnerar en mörk stylesheet."""
        css = self._get_common_dark_elements(bg="#2b2b2b", text="#f0f0f0", base="#3c3c3c", highlight="#555")
        css += """
            QProgressBar::chunk { background-color: #0078d7; }
        """
        return css

    def _get_synthwave_stylesheet(self) -> str:
        """Returnerar en synthwave/outrun-inspirerad stylesheet."""
        css = self._get_common_dark_elements(bg="#2a2139", text="#ffffff", base="#3b2d51", highlight="#ff00ff")
        css += """
            QWidget {
                font-family: "Lucida Console", Monaco, monospace;
            }
            QHeaderView::section, QPushButton, QTabBar::tab:selected {
                color: #000000;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                border: 1px solid #00ffff;
            }
            QProgressBar::chunk {
                background-color: #00ffff;
            }
        """
        return css

    def _get_matrix_stylesheet(self) -> str:
        """Returnerar en Matrix-inspirerad stylesheet."""
        css = self._get_common_dark_elements(bg="#000000", text="#00ff00", base="#0a0a0a", highlight="#1a1a1a")
        css += """
            QWidget {
                font-family: "Courier New", Courier, monospace;
            }
            QTableView, QTextEdit {
                gridline-color: #00ff00;
            }
            QLineEdit, QSpinBox, QComboBox, QHeaderView::section {
                border: 1px solid #00ff00;
            }
            QProgressBar {
                border: 1px solid #00ff00;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
            }
        """
        return css
        
    def _get_dracula_stylesheet(self) -> str:
        """Returnerar en Dracula-inspirerad stylesheet."""
        # Dracula Official Palette
        background = "#282a36"
        current_line = "#44475a"
        foreground = "#f8f8f2"
        comment = "#6272a4"
        green = "#50fa7b"
        pink = "#ff79c6"
        purple = "#bd93f9"

        css = self._get_common_dark_elements(bg=background, text=foreground, base=current_line, highlight=comment)
        css += f"""
            QPushButton {{ background-color: {purple}; color: {foreground}; }}
            QPushButton:hover {{ background-color: {pink}; }}
            QProgressBar::chunk {{ background-color: {green}; }}
            QTableView {{ alternate-background-color: #2c2e3b; }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {pink};
            }}
        """
        return css
