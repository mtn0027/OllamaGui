"""
Custom widgets for the Ollama Chatbot GUI
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from pathlib import Path


class MessageBubble(QFrame):
    """Widget for displaying a chat message bubble"""

    delete_requested = pyqtSignal(object)  # Signal to request deletion

    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text_content = text

        # Get the icons directory path
        self.icons_dir = Path(__file__).parent.parent / "icons"

        self.setup_ui(text)

    def load_icon(self, icon_name):
        """Load an SVG icon from the icons directory"""
        icon_path = self.icons_dir / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))
        else:
            print(f"Warning: Icon not found: {icon_path}")
            return QIcon()

    def setup_ui(self, text):
        """Initialize the message bubble UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Avatar with SVG
        avatar = QPushButton()
        avatar.setFixedSize(40, 40)
        if self.is_user:
            avatar.setIcon(self.load_icon("user.svg"))
        else:
            avatar.setIcon(self.load_icon("robot.svg"))
        avatar.setIconSize(QSize(32, 32))
        avatar.setEnabled(False)  # Make it non-clickable
        avatar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)

        # Message content
        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        message.setMinimumWidth(200)
        message.setMaximumWidth(800)

        # Copy button with SVG
        copy_btn = QPushButton()
        copy_btn.setFixedSize(32, 32)
        copy_btn.setIcon(self.load_icon("copy.svg"))
        copy_btn.setIconSize(QSize(18, 18))
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 122, 255, 0.1);
                border: 1px solid rgba(0, 122, 255, 0.3);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.2);
                border: 1px solid rgba(0, 122, 255, 0.5);
            }
        """)

        # Delete button with SVG
        delete_btn = QPushButton()
        delete_btn.setFixedSize(32, 32)
        delete_btn.setIcon(self.load_icon("delete.svg"))
        delete_btn.setIconSize(QSize(18, 18))
        delete_btn.setToolTip("Delete this message")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 53, 69, 0.1);
                border: 1px solid rgba(220, 53, 69, 0.3);
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(220, 53, 69, 0.25);
                border: 1px solid rgba(220, 53, 69, 0.5);
            }
        """)

        # Layout arrangement
        if self.is_user:
            layout.addStretch()
            layout.addWidget(message)
            layout.addWidget(delete_btn)
            layout.addWidget(copy_btn)
            layout.addWidget(avatar)
            message.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 15px;
                    padding: 12px;
                    font-size: 14px;
                    font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                }
            """)
        else:
            layout.addWidget(avatar)
            layout.addWidget(delete_btn)
            layout.addWidget(copy_btn)
            layout.addWidget(message)
            layout.addStretch()
            message.setStyleSheet("""
                QLabel {
                    background-color: #E9ECEF;
                    color: #212529;
                    border-radius: 15px;
                    padding: 12px;
                    font-size: 14px;
                    font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                }
            """)


class AnimatedSidebar(QFrame):
    """Animated sliding sidebar widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)