"""
Custom widgets for the Ollama Chatbot GUI
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MessageBubble(QFrame):
    """Widget for displaying a chat message bubble"""

    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text_content = text
        self.setup_ui(text)

    def setup_ui(self, text):
        """Initialize the message bubble UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Avatar
        avatar = QLabel("👤" if self.is_user else "🤖")
        avatar.setFont(QFont("Segoe UI Emoji", 16))
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("font-family: 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif;")

        # Message content - USE QLABEL INSTEAD OF QTEXTEDIT
        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        message.setMinimumWidth(200)
        message.setMaximumWidth(800)

        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(30, 30)
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 15px;
            }
        """)

        # Layout arrangement
        if self.is_user:
            layout.addStretch()
            layout.addWidget(message)
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