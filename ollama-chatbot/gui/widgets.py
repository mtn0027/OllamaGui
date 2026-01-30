"""
Custom widgets for the Ollama Chatbot GUI
"""

import re
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QApplication,
                             QVBoxLayout, QTextEdit, QWidget, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
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
        self.search_text = None
        self.is_current_match = False
        self.is_streaming = False  # Track if message is being streamed
        self.streaming_label = None  # Reference to label during streaming

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

            elif part[0] == 'code':
                # Code block - make it wider
                code_widget = CodeBlockWidget(part[1], part[2])
                code_widget.setMinimumWidth(600)  # Minimum width for code blocks
                self.content_layout.addWidget(code_widget)

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

    def update_text(self, new_text, is_streaming=True):
        """Update the message text efficiently without recreating widgets"""
        self.text_content = new_text
        self.is_streaming = is_streaming

        # If streaming, just update the text label without recreating widgets
        if is_streaming and self.streaming_label is not None:
            self.streaming_label.setText(new_text)
            return

        # If not streaming or first time, recreate widgets to parse code blocks
        # Clear existing content widgets
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.streaming_label = None  # Reset reference

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

                # Store reference to first label for streaming updates
                if self.streaming_label is None:
                    self.streaming_label = message

            elif part[0] == 'code':
                # Code block
                code_widget = CodeBlockWidget(part[1], part[2])
                code_widget.setMinimumWidth(600)
                self.content_layout.addWidget(code_widget)

    def highlight_text(self, search_text):
        """Highlight search text in the message"""
        # Don't highlight while streaming to prevent glitches
        if self.is_streaming:
            return
        self.search_text = search_text.lower()
        self._apply_highlight(False)

    def set_current_match(self, is_current):
        """Set whether this is the current search match"""
        self.is_current_match = is_current
        if hasattr(self, 'search_text') and self.search_text:
            self._apply_highlight(is_current)

    def clear_highlight(self):
        """Clear search highlighting"""
        self.search_text = None
        self.is_current_match = False

        # Reset all text widgets to original style
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                # Restore original styling
                if self.is_user:
                    widget.setStyleSheet("""
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
                    widget.setStyleSheet("""
                        QLabel {
                            background-color: #E9ECEF;
                            color: #212529;
                            border-radius: 15px;
                            padding: 12px;
                            font-size: 14px;
                            font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                        }
                    """)
                # Reset to plain text
                widget.setTextFormat(Qt.TextFormat.PlainText)
                widget.setText(widget.text())

    def _apply_highlight(self, is_current):
        """Apply highlighting to matching text"""
        if not hasattr(self, 'search_text') or not self.search_text:
            return

        # Highlight color - orange for current match, yellow for others
        highlight_color = "#FFA500" if is_current else "#FFFF00"

        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                # Get original text
                original_text = self.text_content

                # Create highlighted HTML
                highlighted_text = self._create_highlighted_html(
                    original_text,
                    self.search_text,
                    highlight_color
                )

                # Set HTML text
                widget.setTextFormat(Qt.TextFormat.RichText)
                widget.setText(highlighted_text)

    def _create_highlighted_html(self, text, search_text, highlight_color):
        """Create HTML with highlighted search terms"""
        # Escape HTML special characters in the original text
        text_escaped = (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;')
        )

        # Create a case-insensitive regex pattern
        pattern = re.compile(re.escape(search_text), re.IGNORECASE)

        # Replace matches with highlighted version
        def highlight_match(match):
            matched_text = match.group(0)
            return f'<span style="background-color: {highlight_color}; color: black; padding: 2px 4px; border-radius: 3px; font-weight: bold;">{matched_text}</span>'

        highlighted = pattern.sub(highlight_match, text_escaped)

        # Preserve line breaks
        highlighted = highlighted.replace('\n', '<br>')

        return highlighted


class SearchBar(QWidget):
    """Animated search bar that slides down from top"""

    close_requested = pyqtSignal()
    search_changed = pyqtSignal(str)
    next_requested = pyqtSignal()
    previous_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons_dir = Path(__file__).parent.parent / "icons"
        self.is_visible = False
        self.setup_ui()

    def load_icon(self, icon_name):
        """Load an SVG icon from the icons directory"""
        icon_path = self.icons_dir / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon()

    def setup_ui(self):
        """Setup the search bar UI"""
        self.setFixedHeight(0)  # Start hidden

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        # Search icon/label
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(search_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in chat...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.returnPressed.connect(self.on_next_clicked)
        self.search_input.setFixedHeight(32)
        layout.addWidget(self.search_input)

        # Results counter
        self.results_label = QLabel("")
        self.results_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        self.results_label.setMinimumWidth(80)
        layout.addWidget(self.results_label)

        # Previous button
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(self.load_icon("up.svg"))
        self.prev_btn.setIconSize(QSize(16, 16))
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setToolTip("Previous (Shift+Enter)")
        self.prev_btn.clicked.connect(self.on_previous_clicked)
        layout.addWidget(self.prev_btn)

        # Next button
        self.next_btn = QPushButton()
        self.next_btn.setIcon(self.load_icon("down.svg"))
        self.next_btn.setIconSize(QSize(16, 16))
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setToolTip("Next (Enter)")
        self.next_btn.clicked.connect(self.on_next_clicked)
        layout.addWidget(self.next_btn)

        # Close button
        close_btn = QPushButton()
        close_btn.setIcon(self.load_icon("cross-mark.svg"))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(32, 32)
        close_btn.setToolTip("Close (Esc)")
        close_btn.clicked.connect(self.hide_animated)
        close_btn.setStyleSheet("""
            QPushButton {
                border-radius: 16px;
                background-color: transparent;
                border: 1px solid #dee2e6;
            }
            QPushButton:hover {
                background-color: rgba(220, 53, 69, 0.1);
                border: 1px solid #dc3545;
            }
        """)
        layout.addWidget(close_btn)

        # Apply default light theme
        self.apply_light_theme()

    def show_animated(self):
        """Show the search bar with slide down animation"""
        if self.is_visible:
            return

        self.is_visible = True
        self.setVisible(True)

        # Animation
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(50)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

        # Focus the search input
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_animated(self):
        """Hide the search bar with slide up animation"""
        if not self.is_visible:
            return

        self.is_visible = False

        # Animation
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(50)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.finished.connect(lambda: self.setVisible(False))
        self.animation.start()

        # Clear search
        self.search_input.clear()
        self.close_requested.emit()

    def on_search_changed(self, text):
        """Handle search text change"""
        self.search_changed.emit(text)

    def on_next_clicked(self):
        """Handle next button click"""
        self.next_requested.emit()

    def on_previous_clicked(self):
        """Handle previous button click"""
        self.previous_requested.emit()

    def update_results_label(self, current, total):
        """Update the results counter label"""
        if total == 0:
            self.results_label.setText("No results")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
        else:
            self.results_label.setText(f"{current}/{total}")
            self.prev_btn.setEnabled(total > 1)
            self.next_btn.setEnabled(total > 1)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_animated()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.on_previous_clicked()
        else:
            super().keyPressEvent(event)

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            SearchBar {
                background-color: #2d2d2d;
                border-bottom: 2px solid #404040;
            }
        """)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 16px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
        """)
        self.results_label.setStyleSheet("color: #a0a0a0; font-size: 12px;")

        # Update button styles for dark theme
        button_style = """
            QPushButton {
                border-radius: 16px;
                background-color: transparent;
                border: 1px solid #404040;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.2);
                border: 1px solid #007AFF;
            }
        """
        self.prev_btn.setStyleSheet(button_style)
        self.next_btn.setStyleSheet(button_style)

    def apply_light_theme(self):
        """Apply light theme styling"""
        self.setStyleSheet("""
            SearchBar {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
            }
        """)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #dee2e6;
                border-radius: 16px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
        """)
        self.results_label.setStyleSheet("color: #6c757d; font-size: 12px;")

        # Update button styles for light theme
        button_style = """
            QPushButton {
                border-radius: 16px;
                background-color: transparent;
                border: 1px solid #dee2e6;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 0.1);
                border: 1px solid #007AFF;
            }
        """
        self.prev_btn.setStyleSheet(button_style)
        self.next_btn.setStyleSheet(button_style)


class AnimatedSidebar(QFrame):
    """Animated sliding sidebar widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)