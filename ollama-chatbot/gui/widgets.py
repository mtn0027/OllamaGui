"""
Custom widgets for the Ollama Chatbot GUI
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QApplication
from PyQt6.QtCore import Qt, pyqtProperty
from PyQt6.QtGui import QFont
import markdown


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

        # Message content
        message = QTextEdit()
        message.setReadOnly(True)
        message.setHtml(markdown.markdown(text, extensions=['fenced_code', 'tables']))
        message.setFrameStyle(QFrame.Shape.NoFrame)
        message.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        message.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Auto-resize
        doc_height = message.document().size().height()
        message.setFixedHeight(int(doc_height) + 20)

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
            layout.addWidget(message, 1)
            layout.addWidget(copy_btn)
            layout.addWidget(avatar)
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 15px;
                    padding: 10px;
                    font-size: 14px;
                    font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                }
            """)
        else:
            layout.addWidget(avatar)
            layout.addWidget(copy_btn)
            layout.addWidget(message, 1)
            layout.addStretch()
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #E9ECEF;
                    color: #212529;
                    border-radius: 15px;
                    padding: 10px;
                    font-size: 14px;
                    font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                }
            """)


class AnimatedSidebar(QFrame):
    """Animated sliding sidebar widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._width = 0
        self.target_width = 300
        self.setFixedWidth(0)

    @pyqtProperty(int)
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.setFixedWidth(value)