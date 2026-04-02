"""
Ollama Chatbot GUI - Main Entry Point
Run this file to start the application
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt
from gui.main_window import ChatbotGUI


class SplashScreen(QWidget):
    """Minimal loading splash screen shown while ChatbotGUI initializes.

    Uses a frameless, translucent window so the inner card's rounded corners
    show through to the desktop.  No QGraphicsDropShadowEffect is applied here
    because it is safe (no parent widget has a competing graphics effect), but
    a subtle border is used instead to keep the code simple and portable.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 280)
        self._center_on_screen()
        self._setup_ui()

    def _center_on_screen(self):
        """Position the splash in the center of the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _setup_ui(self):
        """Build the card layout: icon, app name, tagline, progress, status."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Card ─────────────────────────────────────────────────────────────
        # A plain QFrame with border-radius gives rounded corners against the
        # transparent window background without needing any platform-specific mask.
        card = QFrame()
        card.setObjectName("splashCard")
        card.setStyleSheet("""
            QFrame#splashCard {
                background-color: #ffffff;
                border-radius: 20px;
                border: 1px solid #dee2e6;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(48, 40, 48, 36)
        layout.setSpacing(0)

        # App icon loaded from the project root folder
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        _pixmap = QPixmap(str(Path(__file__).parent / "ikonka.png"))
        icon_label.setPixmap(
            _pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        )
        layout.addWidget(icon_label)

        layout.addSpacing(14)

        # App name
        name_label = QLabel("Ollama Chat")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                font-size: 22px;
                font-weight: 700;
                color: #212529;
                background: transparent;
            }
        """)
        layout.addWidget(name_label)

        layout.addSpacing(6)

        # Muted tagline below the app name
        tagline = QLabel("Local AI  ·  Powered by Ollama")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("""
            QLabel {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
                color: #6c757d;
                background: transparent;
            }
        """)
        layout.addWidget(tagline)

        layout.addSpacing(28)

        # Thin accent progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #e9ecef;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        layout.addSpacing(14)

        # Status message — updated via set_status()
        self.status_label = QLabel("Initializing…")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
                color: #6c757d;
                background: transparent;
            }
        """)
        layout.addWidget(self.status_label)

        outer.addWidget(card)

    def set_status(self, message: str, progress: int):
        """Update the status label and progress bar, then flush the event queue
        so the repaint is visible before the next blocking operation starts."""
        self.status_label.setText(message)
        self.progress.setValue(progress)
        QApplication.processEvents()


def main():
    """Initialize and run the application"""
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont('Inter', 10))
        app.setStyleSheet("""
            * {
                font-family: 'Inter', 'Segoe UI', 'Arial', 'Helvetica', sans-serif;
            }
        """)

        # ── Splash screen ─────────────────────────────────────────────────────
        # Show before ChatbotGUI() so the user sees immediate feedback.
        # Status updates bracket the blocking constructor call; processEvents()
        # inside set_status() ensures each message is painted before the next
        # step begins.
        splash = SplashScreen()
        splash.show()
        splash.set_status("Initializing…", 10)

        splash.set_status("Starting Ollama…", 25)

        splash.set_status("Loading interface…", 45)
        window = ChatbotGUI()          # ← main blocking call; all init happens here

        splash.set_status("Restoring sessions…", 80)

        splash.set_status("Ready!", 100)

        # Hand off to the main window and dismiss the splash.
        # repaint() + processEvents() force the first paint of the main window
        # to complete before the splash closes, preventing a white flash on Windows.
        window.show()
        window.repaint()
        QApplication.processEvents()
        splash.close()
        # ─────────────────────────────────────────────────────────────────────

        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()