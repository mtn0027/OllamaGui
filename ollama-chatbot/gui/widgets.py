"""
Custom widgets for the Ollama Chatbot GUI
"""

import re
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QApplication, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
from pathlib import Path


class CodeSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for code blocks"""

    def __init__(self, document, language=""):
        super().__init__(document)
        self.language = language.lower()
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules"""
        self.highlighting_rules = []

        # Keywords format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green
        comment_format.setFontItalic(True)

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))  # Yellow

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green

        # Class format
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4EC9B0"))  # Cyan

        # Common keywords across languages
        keywords = [
            'def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif', 'for', 'while',
            'try', 'except', 'finally', 'with', 'as', 'pass', 'break', 'continue',
            'public', 'private', 'protected', 'static', 'void', 'int', 'String', 'boolean',
            'float', 'double', 'char', 'long', 'short', 'byte', 'const', 'let', 'var',
            'function', 'async', 'await', 'new', 'this', 'super', 'extends', 'implements',
            'interface', 'enum', 'package', 'namespace', 'using', 'typedef', 'struct',
            'union', 'auto', 'extern', 'register', 'sizeof', 'volatile', 'goto',
            'do', 'switch', 'case', 'default', 'true', 'false', 'null', 'None', 'True', 'False',
            'self', 'System', 'out', 'println', 'print', 'main', 'args', 'throws'
        ]

        # Add keyword patterns
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((pattern, keyword_format))

        # Strings (double quotes)
        self.highlighting_rules.append(('"[^"\\\\]*(\\\\.[^"\\\\]*)*"', string_format))

        # Strings (single quotes)
        self.highlighting_rules.append(("'[^'\\\\]*(\\\\.[^'\\\\]*)*'", string_format))

        # Numbers
        self.highlighting_rules.append(('\\b[0-9]+\\.?[0-9]*\\b', number_format))

        # Single-line comments (// and #)
        self.highlighting_rules.append(('//[^\n]*', comment_format))
        self.highlighting_rules.append(('#[^\n]*', comment_format))

        # Functions
        self.highlighting_rules.append(('\\b[A-Za-z0-9_]+(?=\\()', function_format))

        # Classes (capitalized words)
        self.highlighting_rules.append(('\\b[A-Z][A-Za-z0-9_]*\\b', class_format))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        for pattern, format_type in self.highlighting_rules:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_type)


class CodeBlockWidget(QFrame):
    """Widget for displaying code blocks with syntax highlighting"""

    def __init__(self, code, language="", parent=None):
        super().__init__(parent)
        self.code = code
        self.language = language
        self.setup_ui()

    def setup_ui(self):
        """Setup the code block UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with language and copy button
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.3);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 6px 12px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        lang_label = QLabel(self.language if self.language else "code")
        lang_label.setStyleSheet("color: #a0a0a0; font-size: 11px; font-family: 'Consolas', 'Monaco', monospace;")

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(24)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.code))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
        """)

        header_layout.addWidget(lang_label)
        header_layout.addStretch()
        header_layout.addWidget(copy_btn)

        # Code display
        self.code_display = QTextEdit()
        self.code_display.setPlainText(self.code)
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Consolas", 10))
        self.code_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.5;
            }
        """)

        # Apply syntax highlighting
        self.highlighter = CodeSyntaxHighlighter(self.code_display.document(), self.language)

        # Set fixed height based on line count (max 20 lines visible)
        line_count = self.code.count('\n') + 1
        visible_lines = min(line_count, 20)
        self.code_display.setFixedHeight(visible_lines * 20 + 24)

        layout.addWidget(header)
        layout.addWidget(self.code_display)


class MessageBubble(QFrame):
    """Widget for displaying a chat message bubble"""

    delete_requested = pyqtSignal(object)  # Signal to request deletion

    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text_content = text
        self.content_widgets = []  # Store references to content widgets

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

    def parse_markdown_content(self, text):
        """Parse markdown text and create widgets for text and code blocks"""
        # Pattern to match code blocks: ```language\ncode\n``` OR incomplete blocks ```language\ncode (no closing)
        pattern = r'```(\w+)?\n(.*?)(?:```|$)'
        parts = []
        last_end = 0

        for match in re.finditer(pattern, text, re.DOTALL):
            # Add text before code block
            if match.start() > last_end:
                text_before = text[last_end:match.start()].strip()
                if text_before:
                    parts.append(('text', text_before))

            # Add code block
            language = match.group(1) or ''
            code = match.group(2).strip()
            if code:  # Only add if there's actual code content
                parts.append(('code', code, language))

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            text_after = text[last_end:].strip()
            if text_after:
                parts.append(('text', text_after))

        # If no code blocks found, return original text
        if not parts:
            parts.append(('text', text))

        return parts

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

        # Message content container
        self.content_container = QFrame()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        # Parse content for code blocks
        parts = self.parse_markdown_content(text)

        for part in parts:
            if part[0] == 'text':
                # Regular text message
                message = QLabel(part[1])
                message.setWordWrap(True)
                message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                if self.is_user:
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
                self.content_layout.addWidget(message)
                self.content_widgets.append(message)

            elif part[0] == 'code':
                # Code block - make it wider
                code_widget = CodeBlockWidget(part[1], part[2])
                code_widget.setMinimumWidth(600)  # Minimum width for code blocks
                self.content_layout.addWidget(code_widget)
                self.content_widgets.append(code_widget)

        # Copy button
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
            layout.addWidget(self.content_container)
            layout.addWidget(delete_btn)
            layout.addWidget(copy_btn)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(delete_btn)
            layout.addWidget(copy_btn)
            layout.addWidget(self.content_container)
            layout.addStretch()

    def update_text(self, new_text):
        """Update the message text efficiently without recreating widgets"""
        self.text_content = new_text

        # Clear existing content widgets
        for widget in self.content_widgets:
            widget.deleteLater()
        self.content_widgets.clear()

        # Parse and add new content
        parts = self.parse_markdown_content(new_text)

        for part in parts:
            if part[0] == 'text':
                # Regular text message
                message = QLabel(part[1])
                message.setWordWrap(True)
                message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                if self.is_user:
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
                self.content_layout.addWidget(message)
                self.content_widgets.append(message)

            elif part[0] == 'code':
                # Code block
                code_widget = CodeBlockWidget(part[1], part[2])
                code_widget.setMinimumWidth(600)
                self.content_layout.addWidget(code_widget)
                self.content_widgets.append(code_widget)


class AnimatedSidebar(QFrame):
    """Animated sliding sidebar widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)