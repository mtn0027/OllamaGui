"""
Custom widgets for the Ollama Chatbot GUI
"""

import re
from datetime import datetime
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QApplication,
                             QVBoxLayout, QTextEdit, QWidget, QLineEdit, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
from pathlib import Path

from gui.themes import (
    BASE_FONT_FAMILY,
    CODE_FONT_FAMILY,
    LIGHT_TOKENS,
    DARK_TOKENS,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    RADIUS_MD,
    RADIUS_LG,
    SPACE_SM,
    SPACE_MD,
)


class DateSeparator(QWidget):
    """A horizontal date-chip separator, styled like WhatsApp / Telegram."""

    def __init__(self, date_str: str, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.setFixedHeight(36)
        self._setup_ui()
        self.apply_light_theme()

    def _setup_ui(self):
        """Build the left-rule / label / right-rule layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Left horizontal rule
        self._left_line = QFrame()
        self._left_line.setFrameShape(QFrame.Shape.HLine)
        self._left_line.setFrameShadow(QFrame.Shadow.Plain)
        self._left_line.setFixedHeight(1)

        # Date chip label
        self._label = QLabel(self.date_str)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont(BASE_FONT_FAMILY, FONT_SIZE_CAPTION))
        self._label.setSizePolicy(
            self._label.sizePolicy().horizontalPolicy(),
            self._label.sizePolicy().verticalPolicy(),
        )
        self._label.setContentsMargins(SPACE_MD, 2, SPACE_MD, 2)

        # Right horizontal rule
        self._right_line = QFrame()
        self._right_line.setFrameShape(QFrame.Shape.HLine)
        self._right_line.setFrameShadow(QFrame.Shadow.Plain)
        self._right_line.setFixedHeight(1)

        layout.addWidget(self._left_line, 1)
        layout.addWidget(self._label, 0)
        layout.addWidget(self._right_line, 1)

    def _apply_tokens(self, tokens: dict):
        """Apply a token dict to all child elements."""
        line_color = tokens['border_subtle']
        self._left_line.setStyleSheet(f"background-color: {line_color}; border: none;")
        self._right_line.setStyleSheet(f"background-color: {line_color}; border: none;")
        self._label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {tokens['bg_surface_alt']};
                color: {tokens['text_muted']};
                border: 1px solid {tokens['border_subtle']};
                border-radius: {RADIUS_MD}px;
                font-size: {FONT_SIZE_CAPTION}px;
                font-family: {BASE_FONT_FAMILY};
                padding: 2px {SPACE_MD}px;
            }}
            """
        )

    def apply_light_theme(self):
        """Switch to light-theme colors."""
        self._apply_tokens(LIGHT_TOKENS)

    def apply_dark_theme(self):
        """Switch to dark-theme colors."""
        self._apply_tokens(DARK_TOKENS)


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

    def __init__(self, text, is_user, timestamp=None, is_streaming=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text_content = text
        self.search_text = None
        self.is_current_match = False

        # Public streaming flag (read by main_window) and internal guard used
        # by the streaming dispatch path.
        self.is_streaming = is_streaming
        self._is_streaming = False          # set to True by start_streaming()

        # streaming_label is the single QLabel used while tokens arrive.
        # It is created by start_streaming() and destroyed by finalize_streaming().
        self.streaming_label = None

        self.text_labels = []  # Store references to text labels with their content

        # Cache for the last search text applied via _apply_highlight().
        # Prevents re-rendering HTML spans on every keystroke when the term
        # has not changed (only the current-match colour may differ).
        self._last_highlight_text = ""

        # Store timestamp — auto-generate if not provided
        self.timestamp_str = timestamp if timestamp else datetime.now().strftime("%H:%M")

        # Get the icons directory path
        self.icons_dir = Path(__file__).parent.parent / "icons"

        self.setup_ui(text, is_streaming=is_streaming)

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

    def _make_timestamp_label(self):
        """Create a styled timestamp label"""
        ts_label = QLabel(self.timestamp_str)
        ts_label.setStyleSheet(
            f"""
            QLabel {{
                color: rgba(108, 117, 125, 0.75);
                font-size: 10px;
                font-family: {BASE_FONT_FAMILY};
                padding: 2px 4px 0px 4px;
                background-color: transparent;
            }}
            """
        )
        ts_label.setAlignment(
            Qt.AlignmentFlag.AlignRight if self.is_user else Qt.AlignmentFlag.AlignLeft
        )
        return ts_label

    def _make_text_label(self, text):
        """Create a styled, plain-text-format QLabel for a prose segment.

        Using PlainText format tells Qt to skip the HTML auto-detection pass
        on every setText() call, which eliminates measurable overhead at the
        60 fps streaming rate.
        """
        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # Explicitly opt out of HTML parsing; _apply_highlight() switches to
        # RichText only when it needs to inject <span> tags.
        message.setTextFormat(Qt.TextFormat.PlainText)

        if self.is_user:
            message.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {LIGHT_TOKENS['primary']};
                    color: {LIGHT_TOKENS['text_inverse']};
                    border-radius: {RADIUS_LG}px;
                    padding: {SPACE_MD}px;
                    font-size: {FONT_SIZE_BODY}px;
                    font-family: {BASE_FONT_FAMILY};
                }}
                """
            )
        else:
            message.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {LIGHT_TOKENS['bg_surface_alt']};
                    color: {LIGHT_TOKENS['text_primary']};
                    border-radius: {RADIUS_LG}px;
                    padding: {SPACE_MD}px;
                    font-size: {FONT_SIZE_BODY}px;
                    font-family: {BASE_FONT_FAMILY};
                }}
                """
            )
        return message

    def setup_ui(self, text, is_streaming=False):
        """Initialize the message bubble UI.

        Builds the outer frame (avatar, content container, copy/delete buttons)
        regardless of streaming state.  Content population is handled separately:
        - Streaming path: start_streaming() inserts the live QLabel at index 0.
        - Normal path: parse_markdown_content() populates the content_layout here.
        """
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

        # Clear text labels list
        self.text_labels = []

        if is_streaming:
            # Streaming path: content_layout starts empty; start_streaming()
            # inserts the live label at index 0 when the first token arrives.
            self.start_streaming()
        else:
            # Normal path: full markdown parse, build all content widgets now.
            parts = self.parse_markdown_content(text)

            for part in parts:
                if part[0] == 'text':
                    message = self._make_text_label(part[1])
                    self.content_layout.addWidget(message)
                    self.text_labels.append({'widget': message, 'text': part[1]})

                elif part[0] == 'code':
                    # Code block - make it wider
                    code_widget = CodeBlockWidget(part[1], part[2])
                    code_widget.setMinimumWidth(600)
                    self.content_layout.addWidget(code_widget)

            # Timestamp label — sits below all content parts
            self.content_layout.addWidget(self._make_timestamp_label())

        # Copy button
        copy_btn = QPushButton()
        copy_btn.setFixedSize(32, 32)
        copy_btn.setIcon(self.load_icon("copy.svg"))
        copy_btn.setIconSize(QSize(18, 18))
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.text_content))
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

    # ------------------------------------------------------------------
    # Streaming path — zero layout changes during token delivery
    # ------------------------------------------------------------------

    def start_streaming(self):
        """Create the dedicated streaming label and enter streaming mode.

        Called once, either from setup_ui() when the bubble is constructed
        with is_streaming=True, or lazily from stream_text() on the first
        token.  The label is inserted at index 0 so it appears above the
        timestamp (which is not added until finalize_streaming()).
        """
        self._is_streaming = True
        self.is_streaming = True

        # Create a lightweight plain-text label — no HTML parser, no layout
        # invalidation on every setText() call.
        lbl = QLabel("")
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setTextFormat(Qt.TextFormat.PlainText)
        lbl.setContentsMargins(0, 0, 0, 0)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lbl.setStyleSheet(
            f"""
            QLabel {{
                background-color: {LIGHT_TOKENS['bg_surface_alt']};
                color: {LIGHT_TOKENS['text_primary']};
                border-radius: {RADIUS_LG}px;
                padding: {SPACE_MD}px;
                font-size: {FONT_SIZE_BODY}px;
                font-family: {BASE_FONT_FAMILY};
            }}
            """
        )

        self.streaming_label = lbl
        # Insert at position 0; content_layout is empty at this point so
        # this is equivalent to addWidget, but explicit about intent.
        self.content_layout.insertWidget(0, self.streaming_label)

    def stream_text(self, text: str):
        """Update the live streaming label with accumulated response text.

        This is the hot path called at up to 60 fps.  It does exactly one
        thing: setText() on the existing label.  No layout changes, no widget
        creation, no markdown parsing.  Must complete in under 0.1 ms.
        """
        if self.streaming_label is None:
            self.start_streaming()
        self.text_content = text
        self.streaming_label.setText(text)

    def finalize_streaming(self, final_text: str):
        """Tear down the streaming label and render the finished message.

        This is the only place parse_markdown_content() is called for a
        streamed message.  It replaces the plain streaming label with fully
        rendered content including code blocks, then appends the timestamp.
        """
        self._is_streaming = False
        self.is_streaming = False
        self.text_content = final_text

        # Remove and destroy the streaming label
        if self.streaming_label is not None:
            self.content_layout.removeWidget(self.streaming_label)
            self.streaming_label.deleteLater()
            self.streaming_label = None

        # Clear any remaining widgets (safety — should be empty at this point)
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.text_labels = []
        self._last_highlight_text = ""

        # Full markdown parse — only runs once, here, for streamed messages
        parts = self.parse_markdown_content(final_text)

        for part in parts:
            if part[0] == 'text':
                message = self._make_text_label(part[1])
                self.content_layout.addWidget(message)
                self.text_labels.append({'widget': message, 'text': part[1]})

            elif part[0] == 'code':
                code_widget = CodeBlockWidget(part[1], part[2])
                code_widget.setMinimumWidth(600)
                self.content_layout.addWidget(code_widget)

        # Timestamp added once, at the end of the finished message
        self.content_layout.addWidget(self._make_timestamp_label())

    # ------------------------------------------------------------------
    # General text update (called by main_window for both streaming and
    # non-streaming contexts)
    # ------------------------------------------------------------------

    def update_text(self, new_text, is_streaming=True):
        """Update the message text.

        Streaming guard: if _is_streaming is True, delegate immediately to
        stream_text() — zero layout work, zero markdown parsing.

        Finalization: when is_streaming=False, sync the flags and delegate to
        finalize_streaming() which tears down the streaming label, runs the
        full parse, and adds the timestamp exactly once.
        """
        # Sync public attribute so external readers (main_window) stay correct
        self._is_streaming = is_streaming
        self.is_streaming = is_streaming
        self.text_content = new_text

        if self._is_streaming:
            # Hot path — called at 60 fps during streaming
            self.stream_text(new_text)
            return

        # Finalization path — called once when streaming is complete
        self.finalize_streaming(new_text)

    # ------------------------------------------------------------------
    # Search / highlight
    # ------------------------------------------------------------------

    def highlight_text(self, search_text):
        """Highlight search text in the message - only in text labels, not code blocks"""
        # Don't highlight while streaming to prevent glitches
        if self._is_streaming:
            return
        self.search_text = search_text.lower()
        self._apply_highlight(False)

    def set_current_match(self, is_current):
        """Set whether this is the current search match"""
        self.is_current_match = is_current
        if hasattr(self, 'search_text') and self.search_text:
            # Force=True: the search term is unchanged but the highlight colour
            # must update (normal → current or vice versa), so skip the cache.
            self._apply_highlight(is_current, force=True)

    def clear_highlight(self):
        """Clear search highlighting"""
        self.search_text = None
        self.is_current_match = False
        self._last_highlight_text = ""  # Invalidate cache

        # Reset only text labels to original style (not code blocks)
        for label_data in self.text_labels:
            widget = label_data['widget']
            # Restore original styling
            if self.is_user:
                widget.setStyleSheet(
                    f"""
                    QLabel {{
                        background-color: {LIGHT_TOKENS['primary']};
                        color: {LIGHT_TOKENS['text_inverse']};
                        border-radius: {RADIUS_LG}px;
                        padding: {SPACE_MD}px;
                        font-size: {FONT_SIZE_BODY}px;
                        font-family: {BASE_FONT_FAMILY};
                    }}
                    """
                )
            else:
                widget.setStyleSheet(
                    f"""
                    QLabel {{
                        background-color: {LIGHT_TOKENS['bg_surface_alt']};
                        color: {LIGHT_TOKENS['text_primary']};
                        border-radius: {RADIUS_LG}px;
                        padding: {SPACE_MD}px;
                        font-size: {FONT_SIZE_BODY}px;
                        font-family: {BASE_FONT_FAMILY};
                    }}
                    """
                )
            # Restore PlainText format and the original stored content
            widget.setTextFormat(Qt.TextFormat.PlainText)
            widget.setText(label_data['text'])

    def _apply_highlight(self, is_current, force=False):
        """Apply highlighting to matching text - only in text labels.

        Skips re-rendering HTML if the search term is identical to the last
        rendered term and force=False.  set_current_match() passes force=True
        because only the highlight colour changes, not the search term.
        """
        if not hasattr(self, 'search_text') or not self.search_text:
            return

        # Cache check: if the search term hasn't changed and we're not forced
        # (e.g. by a current-match colour update), skip the expensive HTML pass.
        if self.search_text == self._last_highlight_text and not force:
            return

        # Highlight color - orange for current match, yellow for others
        highlight_color = "#FFA500" if is_current else "#FFFF00"

        # Only highlight text labels, not code blocks
        for label_data in self.text_labels:
            widget = label_data['widget']
            text = label_data['text']

            # Check if search text is in this label's text
            if self.search_text in text.lower():
                # Create highlighted HTML
                highlighted_text = self._create_highlighted_html(
                    text,
                    self.search_text,
                    highlight_color
                )

                # Switch to RichText only when injecting HTML spans
                widget.setTextFormat(Qt.TextFormat.RichText)
                widget.setText(highlighted_text)

        # Update cache so identical subsequent calls are skipped
        self._last_highlight_text = self.search_text

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
        # NOTE: Do NOT apply QGraphicsDropShadowEffect here.
        # The parent central widget has a QGraphicsOpacityEffect and Qt cannot
        # nest graphics effects — doing so causes child widgets (input, buttons)
        # to render into a broken offscreen pixmap and appear invisible.

    def load_icon(self, icon_name):
        """Load an SVG icon from the icons directory"""
        icon_path = self.icons_dir / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon()

    _BTN_STYLE = """
        QPushButton {
            background-color: transparent;
            border: 1px solid #ced4da;
            border-radius: 16px;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: rgba(0, 122, 255, 0.12);
            border-color: #007AFF;
        }
        QPushButton:disabled {
            opacity: 0.4;
        }
    """

    def setup_ui(self):
        """Setup the search bar UI"""
        # Height starts at 0 via setMaximumHeight(0) in show_animated;
        # no fixed-height lock needed here (that would break child rendering).
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        # Search icon/label
        search_label = QLabel("🔎")
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
        self.results_label.setMinimumWidth(80)
        layout.addWidget(self.results_label)

        # Previous button — explicit style so global theme doesn't override it
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(self.load_icon("up.svg"))
        self.prev_btn.setIconSize(QSize(16, 16))
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setToolTip("Previous (Shift+Enter)")
        self.prev_btn.setStyleSheet(self._BTN_STYLE)
        self.prev_btn.clicked.connect(self.on_previous_clicked)
        layout.addWidget(self.prev_btn)

        # Next button — explicit style so global theme doesn't override it
        self.next_btn = QPushButton()
        self.next_btn.setIcon(self.load_icon("down.svg"))
        self.next_btn.setIconSize(QSize(16, 16))
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setToolTip("Next (Enter)")
        self.next_btn.setStyleSheet(self._BTN_STYLE)
        self.next_btn.clicked.connect(self.on_next_clicked)
        layout.addWidget(self.next_btn)

        # Close button
        close_btn = QPushButton()
        close_btn.setIcon(self.load_icon("cross-mark.svg"))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(32, 32)
        close_btn.setToolTip("Close (Esc)")
        close_btn.setStyleSheet(self._BTN_STYLE)
        close_btn.clicked.connect(self.hide_animated)
        layout.addWidget(close_btn)

        # Apply default light theme
        self.apply_light_theme()

    def show_animated(self):
        """Show the search bar with slide down animation"""
        if self.is_visible:
            return

        self.is_visible = True

        # Clamp ceiling to 0 before revealing so the widget starts
        # collapsed, then animate the ceiling up to the natural height.
        # Resetting to QWIDGETSIZE_MAX lets the layout breathe freely.
        self.setMaximumHeight(0)
        self.setVisible(True)

        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(52)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(lambda: self.setMaximumHeight(16777215))
        self.animation.start()

        # Focus the search input
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_animated(self):
        """Hide the search bar with slide up animation"""
        if not self.is_visible:
            return

        self.is_visible = False

        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.height())
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)

        def _on_hidden():
            self.setVisible(False)
            self.setMaximumHeight(16777215)  # reset for next show

        self.animation.finished.connect(_on_hidden)
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
        tokens = DARK_TOKENS
        self.setStyleSheet(
            f"""
            SearchBar {{
                background-color: {tokens['bg_surface_alt']};
                border-bottom: 2px solid {tokens['border_subtle']};
            }}
            """
        )
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {tokens['bg_input']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border_subtle']};
                border-radius: 16px;
                padding: {SPACE_SM}px {SPACE_MD}px;
                font-family: {BASE_FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 1px solid {tokens['primary']};
            }}
            """
        )
        self.results_label.setStyleSheet(
            f"color: {tokens['text_muted']}; font-size: {FONT_SIZE_CAPTION}px;"
        )

    def apply_light_theme(self):
        """Apply light theme styling"""
        tokens = LIGHT_TOKENS
        self.setStyleSheet(
            f"""
            SearchBar {{
                background-color: {tokens['bg_surface_alt']};
                border-bottom: 2px solid {tokens['border_subtle']};
            }}
            """
        )
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {tokens['bg_input']};
                color: {tokens['text_primary']};
                border: 1px solid {tokens['border_subtle']};
                border-radius: 16px;
                padding: {SPACE_SM}px {SPACE_MD}px;
                font-family: {BASE_FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 1px solid {tokens['primary']};
            }}
            """
        )
        self.results_label.setStyleSheet(
            f"color: {tokens['text_muted']}; font-size: {FONT_SIZE_CAPTION}px;"
        )


class AnimatedSidebar(QFrame):
    """Animated sliding sidebar widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)