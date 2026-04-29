"""
Main window for the Ollama Chatbot GUI
"""

import json
import requests
import subprocess
import os
import sys
import atexit
import psutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QComboBox, QScrollArea,
                             QLabel, QFrame, QListWidget, QListWidgetItem,
                             QFileDialog, QMessageBox, QInputDialog, QLineEdit,
                             QMenu, QGraphicsOpacityEffect, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut, QPixmap

from gui.widgets import MessageBubble, AnimatedSidebar, SearchBar, DateSeparator
from gui.dialogs import SettingsDialog, ModelDownloadDialog
from gui.themes import LIGHT_THEME, DARK_THEME, build_light_theme, build_dark_theme, LIGHT_TOKENS, DARK_TOKENS, BASE_FONT_FAMILY
from workers.ollama_worker import OllamaWorker


class ChatbotGUI(QMainWindow):
    """Main application window for the Ollama chatbot"""

    def __init__(self):
        super().__init__()

        # Setup data directory
        self.data_dir = Path.home() / ".ollama_chatbot"
        self.data_dir.mkdir(exist_ok=True)
        self.sessions_file = self.data_dir / "chat_sessions.json"
        self.settings_file = self.data_dir / "settings.json"

        # Icons directory
        self.icons_dir = Path(__file__).parent.parent / "icons"

        self.messages = []
        self.current_response = ""
        self.worker = None
        self.ollama_process = None
        self.dark_mode = False
        self.sidebar_open = False
        self.chat_sessions = []
        self.current_session_index = -1
        self.shown_no_models_warning = False

        # Initialize these before init_ui
        self.sidebar = None
        self.opacity_effect = None
        self.animation = None
        self.stop_btn = None
        self.search_bar = None
        self.search_matches = []
        self.current_search_index = -1

        # Sidebar chat search box (set in setup_sidebar, used in apply_theme)
        self.sidebar_search_box = None

        # Theme fade animation handles — kept as instance attributes to prevent
        # garbage collection before the animations complete.
        self._theme_fade_out = None
        self._theme_fade_in = None

        # Streaming state
        self.current_message_bubble = None
        self.current_response_timestamp = ""
        self.current_response_date = ""
        self._token_count = 0  # simple counter for diagnostics; no throttle logic

        # When True, _auto_scroll_tick follows the streamed output.
        # Set to False when the user scrolls up; True when streaming starts
        # or the user clicks the scroll-to-bottom button.
        self._auto_scroll = True

        # Blinking cursor — only the bool is toggled by the timer;
        # the actual setText() is issued by update_response() and _toggle_cursor().
        self._cursor_visible = False
        self._cursor_timer = QTimer()
        self._cursor_timer.setInterval(500)
        self._cursor_timer.timeout.connect(self._toggle_cursor)

        # Dedicated auto-scroll timer: fires every 100 ms while streaming,
        # scrolls only when the user is already near the bottom.
        # Started on the first token in update_response(); stopped in finish_response().
        self._scroll_timer = QTimer()
        self._scroll_timer.setInterval(100)
        self._scroll_timer.timeout.connect(self._auto_scroll_tick)

        # Search debounce timer — search only runs 300 ms after the user
        # stops typing, preventing per-keystroke regex + HTML re-render.
        self._search_debounce_timer = QTimer()
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.setInterval(300)
        self._pending_search_text = ""

        # Session save debounce — avoids a synchronous disk write on every
        # token.  Any code that previously called save_sessions() directly
        # inside hot paths now calls _schedule_save() instead.
        self._save_pending = False
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(2000)
        self._save_timer.timeout.connect(self._flush_save)

        # "Thinking…" animated label timer — cycles dot count 1→2→3→1 at
        # 500 ms intervals while waiting for the first streaming token.
        self._thinking_timer = QTimer()
        self._thinking_timer.setInterval(500)
        self._thinking_timer.timeout.connect(self._tick_thinking)
        self._thinking_dot_count = 0

        # Cached list of ollama psutil.Process objects.  Re-populated only
        # when the cache is empty or a cached process has died, so the full
        # process table walk runs at most once per change, not every second.
        self._ollama_procs: list = []

        # Context length cache — maps model name → context window size (int).
        # Populated lazily by _fetch_context_length(); avoids repeated API calls.
        self._context_length_cache: dict = {}
        self._model_context_length: int = 4096

        self.settings = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt': "You are a helpful AI assistant.",
            'show_resources': False,
            'dark_mode': False,
            'accent_color': '#007AFF',
        }

        # Track Ollama processes for resource monitoring (legacy dict kept for
        # priming state; the new _ollama_procs list drives the fast path).
        self.ollama_processes_tracked = {}

        # Load persisted settings before building the UI
        self.load_settings()

        # Sync dark_mode shortcut from settings
        self.dark_mode = self.settings.get('dark_mode', False)

        # Try to start Ollama
        self.start_ollama()

        self.init_ui()
        self.setup_shortcuts()

        # Load saved sessions
        self.load_saved_sessions()

        # Load models after a brief delay
        QTimer.singleShot(500, self.load_models)

        # Create new session only if no sessions were loaded
        if len(self.chat_sessions) == 0:
            self.create_new_session()
        else:
            # Load the most recent session
            self.chat_list.setCurrentRow(len(self.chat_sessions) - 1)
            self.load_session(self.chat_list.currentItem())
            # Scroll to bottom on startup
            QTimer.singleShot(200, self.scroll_to_bottom)

        # Setup resource monitoring timer
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resource_display)
        self.resource_timer.start(1000)  # Update every second

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def load_settings(self):
        """Load settings from ~/.ollama_chatbot/settings.json"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # Merge saved values into defaults so new keys are always present
                self.settings.update(saved)
                print(f"✓ Settings loaded from {self.settings_file}")
            else:
                print("No saved settings found — using defaults")
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings_to_disk(self):
        """Persist the current settings dict to ~/.ollama_chatbot/settings.json"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            print(f"✓ Settings saved to {self.settings_file}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_icon(self, icon_name):
        """Load an SVG icon from the icons directory"""
        icon_path = self.icons_dir / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))
        else:
            print(f"Warning: Icon not found: {icon_path}")
            return QIcon()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Ollama Chat")
        self.setGeometry(100, 100, 1100, 700)

        icon_path = Path(__file__).parent.parent / "ikonka.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(QPixmap(str(icon_path))))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = AnimatedSidebar()
        self.setup_sidebar()

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.setup_top_bar(content_layout)

        # Add search bar — connect to the debounce slot, not perform_search
        self.search_bar = SearchBar()
        self.search_bar.setVisible(False)
        self.search_bar.search_changed.connect(self._on_search_text_changed)
        self._search_debounce_timer.timeout.connect(
            lambda: self.perform_search(self._pending_search_text)
        )
        self.search_bar.next_requested.connect(self.search_next)
        self.search_bar.previous_requested.connect(self.search_previous)
        self.search_bar.close_requested.connect(self.clear_search)
        content_layout.addWidget(self.search_bar)

        self.setup_chat_area(content_layout)
        self.setup_input_area(content_layout)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_widget)

        self.opacity_effect = QGraphicsOpacityEffect()
        central.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # Apply theme directly on startup — no fade so the initial render
        # doesn't flicker through an animation before the window is shown.
        self._do_apply_theme()

    def setup_top_bar(self, parent_layout):
        """Setup the top bar"""
        top_bar = QHBoxLayout()

        self.toggle_sidebar_btn = QPushButton()
        self.toggle_sidebar_btn.setObjectName("circularBtn")
        self.toggle_sidebar_btn.setIcon(self.load_icon("menu.svg"))
        self.toggle_sidebar_btn.setIconSize(QSize(20, 20))
        self.toggle_sidebar_btn.setFixedSize(45, 45)
        self.toggle_sidebar_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        self.model_label = QLabel("Model: None")
        self.model_label.setObjectName("topBarModelLabel")

        # Resource usage labels (hidden by default)
        self.resource_separator = QLabel("|")
        self.resource_separator.setVisible(False)

        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setVisible(False)

        self.ram_label = QLabel("RAM: 0 MB")
        self.ram_label.setVisible(False)

        # Search button
        search_btn = QPushButton()
        search_btn.setObjectName("circularBtn")
        search_btn.setIcon(self.load_icon("search.svg"))
        search_btn.setIconSize(QSize(20, 20))
        search_btn.setFixedSize(45, 45)
        search_btn.setToolTip("Search in Chat (Ctrl+F)")
        search_btn.clicked.connect(self.toggle_search)

        settings_btn = QPushButton()
        settings_btn.setObjectName("circularBtn")
        settings_btn.setIcon(self.load_icon("settings.svg"))
        settings_btn.setIconSize(QSize(20, 20))
        settings_btn.setFixedSize(45, 45)
        settings_btn.setToolTip("Settings (Ctrl+,)")
        settings_btn.clicked.connect(self.open_settings)

        top_bar.addWidget(self.toggle_sidebar_btn)
        top_bar.addWidget(self.model_label)
        top_bar.addWidget(self.resource_separator)
        top_bar.addWidget(self.cpu_label)
        top_bar.addWidget(self.ram_label)
        top_bar.addStretch()
        top_bar.addWidget(search_btn)
        top_bar.addWidget(settings_btn)

        parent_layout.addLayout(top_bar)

    def setup_chat_area(self, parent_layout):
        """Setup the chat display"""
        # Create a widget to hold both scroll area and button
        chat_wrapper = QWidget()
        chat_wrapper_layout = QVBoxLayout(chat_wrapper)
        chat_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        chat_wrapper_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)

        # Add scroll area to wrapper
        chat_wrapper_layout.addWidget(self.scroll)

        # Scroll to bottom button (floating, positioned absolutely)
        self.scroll_bottom_btn = QPushButton("↓")
        self.scroll_bottom_btn.setParent(chat_wrapper)
        self.scroll_bottom_btn.setObjectName("scrollBottomButton")
        self.scroll_bottom_btn.setFixedSize(50, 50)
        self.scroll_bottom_btn.setToolTip("Scroll to bottom")
        self.scroll_bottom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scroll_bottom_btn.clicked.connect(self.scroll_to_bottom)
        self.scroll_bottom_btn.raise_()  # Bring to front
        self.scroll_bottom_btn.hide()  # Hidden by default

        # Throttled scroll-position check: fires every 150 ms instead of on
        # every pixel of smooth-scroll movement (valueChanged fires ~60 fps).
        # The direct valueChanged connection is intentionally not made here.
        self._scroll_check_timer = QTimer()
        self._scroll_check_timer.setInterval(150)
        self._scroll_check_timer.timeout.connect(self.check_scroll_position)
        self._scroll_check_timer.start()

        self.scroll.verticalScrollBar().sliderMoved.connect(self._on_user_scrolled)
        self.scroll.verticalScrollBar().actionTriggered.connect(self._on_user_scrolled)

        parent_layout.addWidget(chat_wrapper)

    def _is_near_bottom(self) -> bool:
        """Return True when the scroll bar is within 150 px of the maximum."""
        sb = self.scroll.verticalScrollBar()
        return sb.value() >= sb.maximum() - 150

    def _on_user_scrolled(self, *args):
        """Called when the user manually moves the scrollbar.
        Pauses auto-follow so the user can read without the view jumping."""
        if not self._is_near_bottom():
            self._auto_scroll = False
            self.scroll_bottom_btn.show()
            self.position_scroll_button()

    def _auto_scroll_tick(self):
        """Called every 100 ms while streaming; only scrolls if auto-follow is active."""
        if self._auto_scroll:
            self.scroll_to_bottom()

    def check_scroll_position(self):
        """Check if user has scrolled up and show/hide scroll-to-bottom button"""
        scrollbar = self.scroll.verticalScrollBar()
        # Show button if not at bottom (with 100px threshold)
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 100

        if not at_bottom and scrollbar.maximum() > 0:
            self.scroll_bottom_btn.show()
            self.position_scroll_button()
        else:
            self.scroll_bottom_btn.hide()

    def position_scroll_button(self):
        """Position the scroll-to-bottom button in the bottom-right corner"""
        if hasattr(self, 'scroll') and hasattr(self, 'scroll_bottom_btn'):
            # Position relative to scroll area
            scroll_width = self.scroll.width()
            scroll_height = self.scroll.height()
            btn_x = scroll_width - self.scroll_bottom_btn.width() - 20
            btn_y = scroll_height - self.scroll_bottom_btn.height() - 20
            self.scroll_bottom_btn.move(btn_x, btn_y)

    def setup_input_area(self, parent_layout):
        """Setup the input area"""
        # Status row — "Thinking…" label on the left, token counter on the right
        status_row = QHBoxLayout()

        self.thinking_label = QLabel("")
        self.thinking_label.setVisible(False)
        self.thinking_label.setStyleSheet(
            "color: #6c757d; font-size: 12px; padding-left: 4px; background: transparent;"
        )
        status_row.addWidget(self.thinking_label)

        status_row.addStretch()

        # Live token counter — right-aligned, muted, hidden when no content
        self.token_counter_label = QLabel("")
        self.token_counter_label.setVisible(False)
        self.token_counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.token_counter_label.setStyleSheet(
            "color: #6c757d; font-size: 11px; padding-right: 4px; background: transparent;"
        )
        status_row.addWidget(self.token_counter_label)

        parent_layout.addLayout(status_row)

        input_layout = QHBoxLayout()

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self.input_box.setMaximumHeight(100)
        self.input_box.installEventFilter(self)
        self.input_box.textChanged.connect(self._update_token_counter)

        self.send_btn = QPushButton("Send  ")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setIcon(self.load_icon("send.svg"))
        self.send_btn.setIconSize(QSize(18, 18))
        self.send_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Icon on right
        self.send_btn.setFixedSize(100, 60)
        self.send_btn.setToolTip("Send Message")
        self.send_btn.clicked.connect(self.send_message)

        # Stop button (hidden by default)
        self.stop_btn = QPushButton("Stop  ")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setIcon(self.load_icon("stop.svg"))
        self.stop_btn.setIconSize(QSize(18, 18))
        self.stop_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Icon on right
        self.stop_btn.setFixedSize(100, 60)
        self.stop_btn.setToolTip("Stop Generation")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setVisible(False)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.stop_btn)

        parent_layout.addLayout(input_layout)

    def setup_sidebar(self):
        """Setup the sidebar"""
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("💬 Chats")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        # Chat session search box
        self.sidebar_search_box = QLineEdit()
        self.sidebar_search_box.setObjectName("sidebarSearch")
        self.sidebar_search_box.setPlaceholderText("Search chats…")
        self.sidebar_search_box.setFixedHeight(32)
        self.sidebar_search_box.textChanged.connect(self.filter_chat_list)
        layout.addWidget(self.sidebar_search_box)

        new_chat_btn = QPushButton("  New Chat")
        new_chat_btn.setObjectName("primaryButton")
        new_chat_btn.setIcon(self.load_icon("plus.svg"))
        new_chat_btn.setIconSize(QSize(16, 16))
        new_chat_btn.clicked.connect(self.create_new_session)
        new_chat_btn.setToolTip("New Chat (Ctrl+N)")
        layout.addWidget(new_chat_btn)

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_session)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_context_menu)
        self.chat_list.itemDoubleClicked.connect(self.rename_session)
        layout.addWidget(self.chat_list)

        hint_label = QLabel("💡 Right-click or Delete key")
        hint_label.setObjectName("sidebarHint")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        model_label = QLabel("🤖 Model")
        layout.addWidget(model_label)

        self.model_status_label = QLabel("")
        self.model_status_label.setObjectName("mutedLabel")
        self.model_status_label.setVisible(False)
        layout.addWidget(self.model_status_label)

        model_layout = QHBoxLayout()
        self.model_selector = QComboBox()
        self.model_selector.setMinimumHeight(35)
        self.model_selector.currentTextChanged.connect(self.update_model_label)

        refresh_btn = QPushButton()
        refresh_btn.setObjectName("ghostIconButton")
        refresh_btn.setIcon(self.load_icon("refresh.svg"))
        refresh_btn.setIconSize(QSize(20, 20))
        refresh_btn.setFixedSize(38, 38)
        refresh_btn.setToolTip("Refresh Models List")
        refresh_btn.clicked.connect(self.load_models)

        model_layout.addWidget(self.model_selector, 1)
        model_layout.addWidget(refresh_btn)
        layout.addLayout(model_layout)

        download_btn = QPushButton("  Download Model")
        download_btn.setObjectName("primaryButton")
        download_btn.setIcon(self.load_icon("download.svg"))
        download_btn.setIconSize(QSize(16, 16))
        download_btn.setToolTip("Download a New Model from Ollama")
        download_btn.clicked.connect(self.open_download_dialog)
        layout.addWidget(download_btn)

        delete_btn = QPushButton("  Delete Model")
        delete_btn.setObjectName("dangerButton")
        delete_btn.setIcon(self.load_icon("trash.svg"))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setToolTip("Delete Selected Model")
        delete_btn.clicked.connect(self.delete_model)
        layout.addWidget(delete_btn)

        actions_label = QLabel("📁 Actions")
        layout.addWidget(actions_label)

        save_btn = QPushButton("  Save Chat")
        save_btn.setObjectName("secondaryButton")
        save_btn.setIcon(self.load_icon("save.svg"))
        save_btn.setIconSize(QSize(16, 16))
        save_btn.setToolTip("Save Chat to File (Ctrl+S)")
        save_btn.clicked.connect(self.save_chat)
        layout.addWidget(save_btn)

        load_btn = QPushButton("  Load Chat")
        load_btn.setObjectName("secondaryButton")
        load_btn.setIcon(self.load_icon("folder.svg"))
        load_btn.setIconSize(QSize(16, 16))
        load_btn.setToolTip("Load Chat from File (Ctrl+O)")
        load_btn.clicked.connect(self.load_chat)
        layout.addWidget(load_btn)

        clear_btn = QPushButton("  Clear Chat")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.setIcon(self.load_icon("trash.svg"))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setToolTip("Clear Current Chat (Ctrl+K)")
        clear_btn.clicked.connect(self.clear_chat)
        layout.addWidget(clear_btn)

        layout.addStretch()

    def filter_chat_list(self, text: str):
        """Show only chat sessions whose name contains the search string (case-insensitive)."""
        query = text.strip().lower()
        for i, session in enumerate(self.chat_sessions):
            item = self.chat_list.item(i)
            if item is None:
                continue
            item.setHidden(bool(query) and query not in session.get('name', '').lower())

    def toggle_sidebar(self):
        """Toggle sidebar"""
        self.sidebar_open = not self.sidebar_open

        # Use setMaximumWidth animation instead
        self.animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)

        if self.sidebar_open:
            self.animation.setStartValue(0)
            self.animation.setEndValue(300)
        else:
            self.animation.setStartValue(300)
            self.animation.setEndValue(0)

        self.animation.start()

    def toggle_search(self):
        """Toggle search bar visibility"""
        if self.search_bar.is_visible:
            self.search_bar.hide_animated()
        else:
            self.search_bar.show_animated()

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------

    def _on_search_text_changed(self, text: str):
        """Buffer the latest search text and restart the 300 ms debounce timer.

        This slot is connected to search_bar.search_changed instead of
        perform_search directly, so the expensive bubble-iteration + regex +
        HTML re-render only runs once per pause in typing, not on every key.
        """
        self._pending_search_text = text
        self._search_debounce_timer.start()  # restart resets the 300 ms window

    def perform_search(self, search_text):
        """Perform search and highlight matches"""
        # Clear previous highlights
        self.clear_search()

        if not search_text.strip():
            return

        search_text = search_text.lower()
        self.search_matches = []

        # Search through all message bubbles
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, MessageBubble):
                if search_text in widget.text_content.lower():
                    widget.highlight_text(search_text)
                    self.search_matches.append(widget)

        # Update results
        if self.search_matches:
            self.current_search_index = 0
            self.scroll_to_match(0)
            self.search_bar.update_results_label(1, len(self.search_matches))
        else:
            self.current_search_index = -1
            self.search_bar.update_results_label(0, 0)

    def search_next(self):
        """Navigate to next search result"""
        if not self.search_matches:
            return

        self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
        self.scroll_to_match(self.current_search_index)
        self.search_bar.update_results_label(self.current_search_index + 1, len(self.search_matches))

    def search_previous(self):
        """Navigate to previous search result"""
        if not self.search_matches:
            return

        self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
        self.scroll_to_match(self.current_search_index)
        self.search_bar.update_results_label(self.current_search_index + 1, len(self.search_matches))

    def scroll_to_match(self, index):
        """Scroll to the specified search match"""
        if 0 <= index < len(self.search_matches):
            widget = self.search_matches[index]
            self.scroll.ensureWidgetVisible(widget, 50, 50)

            # Highlight current match differently
            for i, match in enumerate(self.search_matches):
                match.set_current_match(i == index)

    def clear_search(self):
        """Clear search highlighting"""
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, MessageBubble):
                widget.clear_highlight()

        self.search_matches = []
        self.current_search_index = -1

    def eventFilter(self, obj, event):
        """Handle events"""
        if obj == self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        """Send message"""
        text = self.input_box.toPlainText().strip()
        if not text or not self.model_selector.currentText():
            return

        # Pre-flight check — verify Ollama is reachable before committing to
        # the send flow.  A fast timeout keeps the UI responsive on failure.
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            QMessageBox.critical(
                self,
                "Ollama Not Running",
                "Ollama is not running. Please start Ollama and try again."
            )
            return

        # Context window warning — estimate total tokens (word count) and warn
        # if the conversation is approaching the model's context limit.
        system_prompt = self.settings['system_prompt']
        estimated = len(system_prompt.split())
        for msg in self.messages:
            estimated += len(msg['content'].split())
        estimated += len(text.split())

        context = self._model_context_length
        pct = (estimated / context * 100) if context > 0 else 0

        if pct > 80:
            warn_box = QMessageBox(self)
            warn_box.setWindowTitle("Context Window Warning")
            warn_box.setText(
                f"The conversation is using approximately {pct:.0f}% of this model's context window "
                f"(~{estimated} / {context} tokens).\n\n"
                f"Sending may cause the model to lose earlier context or produce truncated responses.\n\n"
                f"Send anyway?"
            )
            send_anyway_btn = warn_box.addButton("Send Anyway", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = warn_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            warn_box.exec()
            if warn_box.clickedButton() == cancel_btn:
                return

        self.add_message(text, True)
        self.input_box.clear()
        self.input_box.setEnabled(False)
        self.send_btn.setVisible(False)
        self.stop_btn.setVisible(True)

        self.current_response = ""

        # Build the messages list for multi-turn context from self.messages
        # (already updated by add_message above) and pass to OllamaWorker
        messages_to_send = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

        self.worker = OllamaWorker(
            self.model_selector.currentText(),
            messages_to_send,
            self.settings['system_prompt'],
            self.settings['temperature'],
            self.settings['max_tokens']
        )
        self.worker.token_received.connect(self.update_response)
        self.worker.finished.connect(self.finish_response)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

        # Show the animated "Thinking…" label while waiting for the first token
        self._start_thinking()

    # ------------------------------------------------------------------
    # "Thinking…" animated label helpers
    # ------------------------------------------------------------------

    def _start_thinking(self):
        """Show the thinking label and start the dot-cycling animation."""
        self._thinking_dot_count = 1
        self.thinking_label.setText("Thinking.")
        self.thinking_label.setVisible(True)
        self._thinking_timer.start()

    def _stop_thinking(self):
        """Instantly hide the thinking label and stop its timer."""
        self._thinking_timer.stop()
        self.thinking_label.setVisible(False)
        self.thinking_label.setText("")

    def _tick_thinking(self):
        """Timer slot: cycle dot count 1 → 2 → 3 → 1 and update the label."""
        self._thinking_dot_count = self._thinking_dot_count % 3 + 1
        self.thinking_label.setText("Thinking" + "." * self._thinking_dot_count)

    # ------------------------------------------------------------------
    # Blinking cursor helpers
    # ------------------------------------------------------------------

    def _toggle_cursor(self):
        """500 ms timer slot — toggles the cursor bool and pushes one setText().

        The cursor blink is completely decoupled from the token stream.
        This fires at most twice per second and always calls stream_text()
        on the bubble, which is a single QLabel.setText() call.
        """
        self._cursor_visible = not self._cursor_visible
        if self.current_message_bubble is not None:
            display_text = self.current_response
            if self._cursor_visible:
                display_text += "▋"
            self.current_message_bubble.stream_text(display_text)

    def _start_cursor(self):
        """Start the 500 ms blinking cursor timer."""
        self._cursor_visible = True
        self._cursor_timer.start()

    def _stop_cursor(self):
        """Stop the blinking cursor and reset the visible flag."""
        self._cursor_timer.stop()
        self._cursor_visible = False

    # ------------------------------------------------------------------
    # Context length helpers
    # ------------------------------------------------------------------

    def _fetch_context_length(self, model: str) -> int:
        """Fetch the context window size for a model from the Ollama API.

        Results are cached in self._context_length_cache so the API is only
        called once per model per session.  Falls back to 4096 on any error
        or missing key.
        """
        if model in self._context_length_cache:
            return self._context_length_cache[model]
        try:
            resp = requests.post(
                "http://localhost:11434/api/show",
                json={"name": model},
                timeout=5
            )
            length = resp.json()["model_info"]["llama.context_length"]
            self._context_length_cache[model] = int(length)
            return int(length)
        except Exception:
            self._context_length_cache[model] = 4096
            return 4096

    # ------------------------------------------------------------------
    # Token counter helpers
    # ------------------------------------------------------------------

    def _update_token_counter(self):
        """Recompute the estimated token usage and update the counter label.

        Estimation uses word count (len(text.split())) across the system
        prompt, all stored messages, and the current input box text.
        Label is hidden when there is no content to show.
        """
        tokens = DARK_TOKENS if self.dark_mode else LIGHT_TOKENS

        system_prompt = self.settings.get('system_prompt', '')
        estimated = len(system_prompt.split())
        for msg in self.messages:
            estimated += len(msg['content'].split())
        current_input = self.input_box.toPlainText() if hasattr(self, 'input_box') else ""
        estimated += len(current_input.split())

        if estimated == 0:
            self.token_counter_label.setVisible(False)
            return

        context = self._model_context_length
        pct = (estimated / context * 100) if context > 0 else 0

        self.token_counter_label.setVisible(True)
        self.token_counter_label.setText(f"~{estimated} / {context} tokens ({pct:.0f}%)")

        if pct < 80:
            color = tokens['text_muted']
        elif pct <= 100:
            color = "#FF9500"
        else:
            color = tokens['danger']

        self.token_counter_label.setStyleSheet(
            f"color: {color}; font-size: 11px; padding-right: 4px; background: transparent;"
        )

    # ------------------------------------------------------------------
    # Theme helpers
    # ------------------------------------------------------------------

    def _do_apply_theme(self):
        """Apply the current theme immediately, with no animation.

        Contains the full stylesheet-swap and child-widget re-theming logic.
        Called directly on startup and session load to avoid flickering.
        The opacity is always reset to 1.0 first so a stranded animation
        can never leave the UI partially transparent.
        """
        # Guard: restore full opacity in case a previous animation was
        # interrupted and left the effect at a value below 1.0.
        if self.opacity_effect is not None:
            self.opacity_effect.setOpacity(1.0)

        accent = self.settings.get('accent_color', '#007AFF')
        if self.dark_mode:
            self.setStyleSheet(build_dark_theme(accent))
            tokens = DARK_TOKENS
        else:
            self.setStyleSheet(build_light_theme(accent))
            tokens = LIGHT_TOKENS

        if self.dark_mode:
            input_bg = "#2d2d2d"
            input_border = "#6a6a6a"
        else:
            input_bg = "#ffffff"
            input_border = tokens['border_strong']

        self.input_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {input_bg};
                color: {tokens['text_primary']};
                border: 2px solid {input_border};
                border-radius: 20px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: {BASE_FONT_FAMILY};
            }}
        """)

        if self.search_bar:
            if self.dark_mode:
                self.search_bar.apply_dark_theme()
            else:
                self.search_bar.apply_light_theme()

        # Style the sidebar search box with the correct token colors
        if self.sidebar_search_box is not None:
            self.sidebar_search_box.setStyleSheet(
                f"""
                QLineEdit#sidebarSearch {{
                    background-color: {tokens['bg_input']};
                    color: {tokens['text_primary']};
                    border: 1px solid {tokens['border_subtle']};
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 12px;
                }}
                QLineEdit#sidebarSearch:focus {{
                    border: 1px solid {tokens['primary']};
                    background-color: {tokens['bg_surface']};
                }}
                QLineEdit#sidebarSearch::placeholder {{
                    color: {tokens['text_muted']};
                }}
                """
            )

        # Re-theme any DateSeparator widgets already in the chat layout
        if hasattr(self, 'chat_layout'):
            for i in range(self.chat_layout.count()):
                widget = self.chat_layout.itemAt(i).widget()
                if isinstance(widget, DateSeparator):
                    if self.dark_mode:
                        widget.apply_dark_theme()
                    else:
                        widget.apply_light_theme()

        # Keep the thinking label color in sync with the active theme
        if hasattr(self, 'thinking_label'):
            muted = tokens['text_muted']
            self.thinking_label.setStyleSheet(
                f"color: {muted}; font-size: 12px; padding-left: 4px; background: transparent;"
            )

        # Refresh the token counter label color for the new theme
        if hasattr(self, 'token_counter_label'):
            self._update_token_counter()

    def _animate_theme_change(self, callback):
        """Fade opacity 1.0 → 0.85, swap the theme, then fade back to 1.0.

        Both animation objects are stored as instance attributes so Python's
        garbage collector cannot destroy them before they finish.  Any
        animation already in progress is stopped before new ones are created
        to prevent two animations fighting over the same opacity_effect.
        """
        if self.opacity_effect is None:
            # Fallback: no effect attached yet, apply immediately
            callback()
            return

        # Stop any in-progress fade to avoid concurrent animation conflicts
        if (self._theme_fade_out is not None and
                self._theme_fade_out.state() == QPropertyAnimation.State.Running):
            self._theme_fade_out.stop()
        if (self._theme_fade_in is not None and
                self._theme_fade_in.state() == QPropertyAnimation.State.Running):
            self._theme_fade_in.stop()

        # Fade out: 1.0 → 0.85 over 120 ms
        self._theme_fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._theme_fade_out.setDuration(120)
        self._theme_fade_out.setStartValue(1.0)
        self._theme_fade_out.setEndValue(0.85)
        self._theme_fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_out_finished():
            # Apply the actual theme change at the darkest point
            callback()

            # Fade back in: 0.85 → 1.0 over 120 ms
            self._theme_fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            self._theme_fade_in.setDuration(120)
            self._theme_fade_in.setStartValue(0.85)
            self._theme_fade_in.setEndValue(1.0)
            self._theme_fade_in.setEasingCurve(QEasingCurve.Type.InCubic)
            self._theme_fade_in.start()

        self._theme_fade_out.finished.connect(_on_fade_out_finished)
        self._theme_fade_out.start()

    def apply_theme(self):
        """Apply the current theme with a smooth opacity fade.

        Call this when the user explicitly changes the theme (settings dialog,
        keyboard shortcut). For silent startup rendering use _do_apply_theme()
        directly to avoid an unnecessary animation before the window is shown.
        """
        self._animate_theme_change(self._do_apply_theme)

    # ------------------------------------------------------------------
    # Date separator helpers
    # ------------------------------------------------------------------

    def _format_date_label(self, iso_date: str) -> str:
        """Convert an ISO date string (YYYY-MM-DD) to a human-readable label."""
        try:
            d = datetime.strptime(iso_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            if d == today:
                return "Today"
            if (today - d).days == 1:
                return "Yesterday"
            return d.strftime("%A, %d %B %Y")
        except Exception:
            return iso_date

    def _insert_date_separator(self, iso_date: str):
        """Insert a DateSeparator widget at the current end of chat_layout."""
        label = self._format_date_label(iso_date)
        sep = DateSeparator(label)
        if self.dark_mode:
            sep.apply_dark_theme()
        else:
            sep.apply_light_theme()
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, sep)

    def _last_message_date(self) -> str:
        """Return the ISO date string of the last message, or '' if none."""
        for msg in reversed(self.messages):
            if msg.get('date'):
                return msg['date']
        return ''

    # ------------------------------------------------------------------
    # Session save helpers
    # ------------------------------------------------------------------

    def _schedule_save(self):
        """Mark a save as pending and (re)start the 2-second debounce timer.

        Calling this instead of save_sessions() directly prevents a
        synchronous disk write on every message / token in the hot path.
        The timer is restarted on each call so rapid changes coalesce into
        a single write that happens 2 s after the last change.
        """
        self._save_pending = True
        self._save_timer.start()  # restart resets the 2 s window

    def _flush_save(self):
        """Timer callback: write sessions to disk and clear the pending flag."""
        if self._save_pending:
            self.save_sessions()
            self._save_pending = False

    # ------------------------------------------------------------------

    def add_message(self, text, is_user):
        """Add message"""
        now = datetime.now()
        timestamp = now.strftime("%H:%M")
        iso_date = now.strftime("%Y-%m-%d")

        # Insert a date separator when the day changes (or for the first message)
        last_date = self._last_message_date()
        if iso_date != last_date:
            self._insert_date_separator(iso_date)

        bubble = MessageBubble(text, is_user, timestamp=timestamp)

        # Connect delete signal for ALL messages (user and AI)
        bubble.delete_requested.connect(self.delete_message)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.messages.append({
            "role": "user" if is_user else "assistant",
            "content": text,
            "timestamp": timestamp,
            "date": iso_date,
        })

        if self.current_session_index >= 0:
            self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
            if len(self.messages) == 1:
                preview = text[:30] + "..." if len(text) > 30 else text
                self.chat_sessions[self.current_session_index]['name'] = preview
                item = self.chat_list.item(self.current_session_index)
                if item:
                    item.setText(f"{preview}\n{self.chat_sessions[self.current_session_index]['timestamp']}")

            # Debounced save — avoids a synchronous disk write per message
            self._schedule_save()

        QTimer.singleShot(100, self.scroll_to_bottom)

    def delete_message(self, bubble):
        """Delete a message (user or AI)"""
        message_type = "user message" if bubble.is_user else "AI message"
        reply = QMessageBox.question(
            self,
            'Delete Message',
            f'Delete this {message_type}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Find the message in the layout and messages list
            for i in range(self.chat_layout.count()):
                widget = self.chat_layout.itemAt(i).widget()
                if widget == bubble:
                    # Remove from UI
                    self.chat_layout.removeWidget(bubble)
                    bubble.deleteLater()

                    # Find and remove from messages list
                    # Count only message bubbles before this one
                    message_index = 0
                    for j in range(i):
                        w = self.chat_layout.itemAt(j).widget()
                        if isinstance(w, MessageBubble):
                            message_index += 1

                    # Remove from messages list
                    if message_index < len(self.messages):
                        del self.messages[message_index]

                    # Update session
                    if self.current_session_index >= 0:
                        self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
                        self.save_sessions()

                    break

    def update_response(self, token):
        """Append token and push the updated text to the streaming bubble.

        Single responsibility: accumulate text, call stream_text(), count.
        No scroll logic, no QTimer calls, no markdown detection, no throttle.
        Bubble creation and timer start happen exactly once on the first token.
        """
        self.current_response += token
        self._token_count += 1

        if self.current_message_bubble is None:
            # First token — hide the thinking label, create the bubble, start timers
            self._stop_thinking()
            now = datetime.now()
            self.current_response_timestamp = now.strftime("%H:%M")
            self.current_response_date = now.strftime("%Y-%m-%d")
            self.current_message_bubble = MessageBubble(
                "", False,
                timestamp=self.current_response_timestamp,
                is_streaming=True,
            )
            self.current_message_bubble.delete_requested.connect(self.delete_message)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.current_message_bubble)
            self._auto_scroll = True
            self._start_cursor()
            self._scroll_timer.start()

        display_text = self.current_response + ("▋" if self._cursor_visible else "")
        self.current_message_bubble.stream_text(display_text)

    def finish_response(self):
        """Finalize the streamed response: run the full markdown parse once."""
        # Stop cursor and scroll timers
        self._stop_cursor()
        self._scroll_timer.stop()

        if self.current_message_bubble is not None:
            # Replace the streaming label with fully-rendered markdown content
            self.current_message_bubble.finalize_streaming(self.current_response)

        # Reset streaming state
        bubble = self.current_message_bubble
        self.current_message_bubble = None
        self._token_count = 0

        # Persist the completed assistant message
        if self.current_response and len(self.messages) > 0 and self.messages[-1]["role"] == "user":
            self.messages.append({
                "role": "assistant",
                "content": self.current_response,
                "timestamp": self.current_response_timestamp,
                "date": self.current_response_date,
            })

            if self.current_session_index >= 0:
                self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
                self._schedule_save()

        self.current_response = ""
        self.input_box.setEnabled(True)
        self.send_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.input_box.setFocus()

        # One final scroll to show the complete response
        self.scroll_to_bottom()

        # Refresh token counter after the response is stored
        self._update_token_counter()

    def stop_generation(self):
        """Stop the AI generation"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

            # Stop cursor, scroll, and thinking timers
            self._stop_cursor()
            self._scroll_timer.stop()
            self._stop_thinking()

            # Finalize whatever was generated so far
            if self.current_response and self.current_message_bubble is not None:
                stopped_text = self.current_response + "\n\n[Generation stopped by user]"
                self.current_message_bubble.finalize_streaming(stopped_text)

                if len(self.messages) > 0 and self.messages[-1]["role"] == "user":
                    self.messages.append({
                        "role": "assistant",
                        "content": self.current_response + " [Stopped]",
                        "timestamp": self.current_response_timestamp,
                        "date": self.current_response_date,
                    })

                    if self.current_session_index >= 0:
                        self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
                        self.save_sessions()

            # Reset streaming state
            self.current_message_bubble = None
            self._token_count = 0
            self.current_response = ""
            self.input_box.setEnabled(True)
            self.send_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.input_box.setFocus()

    def handle_error(self, error):
        """Handle error"""
        self._stop_cursor()
        self._scroll_timer.stop()
        self._stop_thinking()
        QMessageBox.critical(self, "Error", f"Failed: {error}")
        self.current_response = ""
        self.current_message_bubble = None
        self._token_count = 0
        self.input_box.setEnabled(True)
        self.send_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.input_box.setFocus()

    def scroll_to_bottom(self):
        """Scroll to bottom and re-enable auto-follow."""
        self._auto_scroll = True
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        self.scroll_bottom_btn.hide()  # Hide button after scrolling

    def load_models(self):
        """Load models"""
        self.model_selector.clear()
        self.model_selector.addItem("⏳ Loading...")
        self.model_selector.setEnabled(False)

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]

            self.model_selector.clear()

            if not models:
                self.model_selector.addItem("⚠️ No models")
                self.model_status_label.setText("Click 📥 Download")
                self.model_status_label.setVisible(True)
            else:
                self.model_selector.setEnabled(True)
                self.model_selector.addItems(models)
                self.model_status_label.setText(f"✓ {len(models)} model(s)")
                self.model_status_label.setVisible(True)
                self.update_model_label()

        except requests.exceptions.ConnectionError:
            self.model_selector.clear()
            self.model_selector.addItem("❌ Ollama not running")
            self.model_status_label.setText("Start Ollama first")
            self.model_status_label.setVisible(True)

    def update_model_label(self):
        """Update model label"""
        model = self.model_selector.currentText()
        self.model_label.setText(f"Model: {model if model else 'None'}")
        if model:
            self._model_context_length = self._fetch_context_length(model)
        if self.current_session_index >= 0:
            self.chat_sessions[self.current_session_index]['model'] = model
            self.save_sessions()

    def update_resource_display(self):
        """Update CPU and RAM usage display in top bar for Ollama server.

        Uses a cached list of psutil.Process objects (_ollama_procs) so the
        full process-table walk (psutil.process_iter) only runs when the cache
        is empty or a previously found process has died.
        """
        if not self.settings.get('show_resources', False):
            self.resource_separator.setVisible(False)
            self.cpu_label.setVisible(False)
            self.ram_label.setVisible(False)
            return

        try:
            logical_cores = psutil.cpu_count(logical=True) or 1

            # ── Cache validity check ──────────────────────────────────
            # Keep the cached list if every entry is still running.
            # Re-scan the full process table only on first call or after a
            # process death, which happens at most once per Ollama restart.
            # Count live ollama processes without fetching full info (cheap)
            live_ollama_count = sum(
                1 for p in psutil.process_iter(['name'])
                if p.info['name'] and 'ollama' in p.info['name'].lower()
            )

            # Cache is valid only if all cached processes are still running AND
            # no new ollama processes have appeared (e.g. model runner spawning)
            cache_valid = (
                bool(self._ollama_procs)
                and len(self._ollama_procs) == live_ollama_count
                and all(p['process'].is_running() for p in self._ollama_procs)
            )

            if not cache_valid:
                # Full scan — expensive but infrequent
                new_procs = []
                for proc in psutil.process_iter(['name', 'pid']):
                    try:
                        if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                            pid = proc.info['pid']
                            if pid not in self.ollama_processes_tracked:
                                p = psutil.Process(pid)
                                p.cpu_percent()  # Prime the measurement
                                self.ollama_processes_tracked[pid] = {
                                    'process': p,
                                    'primed': False,
                                }
                            new_procs.append(self.ollama_processes_tracked[pid])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Purge stale entries from the tracking dict
                live_pids = {d['process'].pid for d in new_procs}
                for pid in list(self.ollama_processes_tracked.keys()):
                    if pid not in live_pids:
                        del self.ollama_processes_tracked[pid]

                self._ollama_procs = new_procs

            ollama_processes = self._ollama_procs

            if ollama_processes:
                total_cpu_raw = 0.0
                total_ram = 0.0

                # Sum resources from all ollama processes
                for proc_data in ollama_processes:
                    try:
                        proc = proc_data['process']

                        # Get CPU percentage (psutil returns per-core usage)
                        cpu = proc.cpu_percent(interval=None)

                        # Skip first real measurement after priming
                        if not proc_data['primed']:
                            proc_data['primed'] = True
                            cpu = 0.0

                        total_cpu_raw += cpu

                        # RAM: use rss (Working Set) — always accessible without
                        # elevated privileges and matches Task Manager's value.
                        if sys.platform == "win32":
                            mem_info = proc.memory_info()
                            ram = mem_info.rss / (1024 * 1024)
                        else:
                            mem_info = proc.memory_info()
                            ram = mem_info.rss / (1024 * 1024)

                        total_ram += ram

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process died mid-tick — invalidate cache next cycle
                        self._ollama_procs = []
                        continue

                # Normalise from per-core percentage to percentage of total system CPU,
                # matching the value shown in Windows Task Manager's Processes tab.
                total_cpu = total_cpu_raw / logical_cores

                # Update labels
                self.cpu_label.setText(f"CPU: {total_cpu:.1f}%")
                self.ram_label.setText(f"RAM: {total_ram:.0f} MB")

                # Show labels
                self.resource_separator.setVisible(True)
                self.cpu_label.setVisible(True)
                self.ram_label.setVisible(True)

            else:
                # Ollama not found
                self.cpu_label.setText("Ollama: Not running")
                self.ram_label.setText("")
                self.resource_separator.setVisible(True)
                self.cpu_label.setVisible(True)
                self.ram_label.setVisible(False)

        except Exception as e:
            print(f"Error updating resource display: {e}")
            self.cpu_label.setText("CPU: N/A")
            self.ram_label.setText("RAM: N/A")
            self.resource_separator.setVisible(True)
            self.cpu_label.setVisible(True)
            self.ram_label.setVisible(True)

    def create_new_session(self):
        """Create new session"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        session = {
            'name': f"Chat {len(self.chat_sessions) + 1}",
            'timestamp': timestamp,
            'messages': [],
            'model': self.model_selector.currentText() if self.model_selector.count() > 0 else ""
        }
        self.chat_sessions.append(session)
        self.current_session_index = len(self.chat_sessions) - 1

        item = QListWidgetItem(f"{session['name']}\n{timestamp}")
        self.chat_list.addItem(item)
        self.chat_list.setCurrentItem(item)
        self.messages = []  # Reset message list so stale data from previous session doesn't bleed in
        self.clear_chat_display()

        # Auto-save
        self.save_sessions()

    def load_session(self, item):
        """Load session"""
        index = self.chat_list.row(item)
        self.current_session_index = index
        session = self.chat_sessions[index]

        if session['model']:
            idx = self.model_selector.findText(session['model'])
            if idx >= 0:
                self.model_selector.setCurrentIndex(idx)

        self.clear_chat_display()
        self.messages = session['messages'].copy()

        last_date = ''
        for msg in self.messages:
            iso_date = msg.get('date', '')

            # Insert a date separator when the day changes (skip if no date field)
            if iso_date and iso_date != last_date:
                self._insert_date_separator(iso_date)
                last_date = iso_date

            saved_timestamp = msg.get('timestamp', '')
            bubble = MessageBubble(msg['content'], msg['role'] == 'user', timestamp=saved_timestamp)
            bubble.delete_requested.connect(self.delete_message)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        # Scroll to bottom after loading messages
        QTimer.singleShot(100, self.scroll_to_bottom)

        # Refresh token counter after loading a session
        self._update_token_counter()

    def show_chat_context_menu(self, position):
        """Show context menu"""
        item = self.chat_list.itemAt(position)
        if not item:
            return

        menu = QMenu()
        rename_action = QAction(self.load_icon("edit.svg"), "Rename", self)
        delete_action = QAction(self.load_icon("trash.svg"), "Delete", self)

        rename_action.triggered.connect(lambda: self.rename_session(item))
        delete_action.triggered.connect(self.delete_session)

        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec(self.chat_list.mapToGlobal(position))

    def rename_session(self, item=None):
        """Rename session"""
        if item is None:
            item = self.chat_list.currentItem()
        if not item:
            return

        index = self.chat_list.row(item)
        current_name = self.chat_sessions[index]['name']

        new_name, ok = QInputDialog.getText(self, 'Rename', 'Name:', QLineEdit.EchoMode.Normal, current_name)

        if ok and new_name.strip():
            self.chat_sessions[index]['name'] = new_name.strip()
            timestamp = self.chat_sessions[index]['timestamp']
            item.setText(f"{new_name.strip()}\n{timestamp}")

            # Auto-save
            self.save_sessions()

    def delete_session(self):
        """Delete session"""
        if self.current_session_index < 0:
            return

        reply = QMessageBox.question(self, 'Delete', 'Delete chat?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.chat_sessions[self.current_session_index]
            self.chat_list.takeItem(self.current_session_index)

            if len(self.chat_sessions) == 0:
                self.create_new_session()
            else:
                self.current_session_index = max(0, self.current_session_index - 1)
                self.chat_list.setCurrentRow(self.current_session_index)
                self.load_session(self.chat_list.currentItem())

            # Auto-save
            self.save_sessions()

    def delete_session_with_key(self):
        """Delete currently selected chat session with Delete key"""
        current_item = self.chat_list.currentItem()
        if current_item and self.current_session_index >= 0:
            self.delete_session()

    def open_download_dialog(self):
        """Open download dialog"""
        dialog = ModelDownloadDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_models()
            QTimer.singleShot(500, self.load_models)

    def delete_model(self):
        """Delete model"""
        model = self.model_selector.currentText()
        if not model:
            return

        reply = QMessageBox.question(self, 'Delete', f'Delete "{model}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                requests.delete("http://localhost:11434/api/delete", json={"name": model})
                QMessageBox.information(self, "Success", "Deleted!")
                self.load_models()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def clear_chat(self):
        """Clear chat"""
        # Add confirmation dialog
        reply = QMessageBox.question(
            self,
            'Clear Chat',
            'Are you sure you want to clear the current chat? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.clear_chat_display()
            self.messages.clear()
            if self.current_session_index >= 0:
                self.chat_sessions[self.current_session_index]['messages'] = []
                # Auto-save
                self.save_sessions()

    def clear_chat_display(self):
        """Clear display.

        Suppresses viewport repaints during the removal loop so that Qt does
        not issue a repaint for every individual widget deletion.  This
        eliminates the stutter visible when clearing large sessions.
        """
        viewport = self.scroll.viewport()
        viewport.setUpdatesEnabled(False)
        for i in reversed(range(self.chat_layout.count() - 1)):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                self.chat_layout.removeWidget(widget)
                widget.deleteLater()
        viewport.setUpdatesEnabled(True)

    def save_chat(self):
        """Save chat"""
        if not self.messages:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json);;Markdown (*.md)")
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump({'timestamp': datetime.now().isoformat(),
                                  'model': self.model_selector.currentText(),
                                  'messages': self.messages}, f, indent=2)
                else:
                    with open(filename, 'w') as f:
                        f.write(f"# Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                        for msg in self.messages:
                            role = "**You:**" if msg['role'] == 'user' else "**AI:**"
                            ts = msg.get('timestamp', '')
                            ts_suffix = f" _{ts}_" if ts else ""
                            f.write(f"{role}{ts_suffix}\n{msg['content']}\n\n---\n\n")
                QMessageBox.information(self, "Success", "Saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def load_chat(self):
        """Load chat"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load", "", "JSON (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                session = {
                    'name': data['messages'][0]['content'][:30] + "..." if data['messages'] else "Loaded",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'messages': data['messages'],
                    'model': data.get('model', '')
                }
                self.chat_sessions.append(session)
                self.current_session_index = len(self.chat_sessions) - 1

                item = QListWidgetItem(f"{session['name']}\n{session['timestamp']}")
                self.chat_list.addItem(item)
                self.chat_list.setCurrentItem(item)
                self.load_session(item)
                self.save_sessions()

                QMessageBox.information(self, "Success", "Loaded!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def open_settings(self):
        """Open settings — pass self so the dialog can read and write all settings"""
        dialog = SettingsDialog(self, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Sync dark_mode shortcut from the (possibly updated) settings dict
            self.dark_mode = self.settings.get('dark_mode', False)
            # Re-apply theme with animated fade (user-initiated change)
            self.apply_theme()
            # Update resource display visibility immediately
            self.update_resource_display()
            # Persist new settings to disk
            self.save_settings_to_disk()

    def _kill_process_tree(self, proc):
        """Kill a process and all of its children using psutil (cross-platform)."""
        try:
            parent = psutil.Process(proc.pid)
            children = parent.children(recursive=True)

            # Send terminate to everyone first for a clean shutdown
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            parent.terminate()

            # Give them up to 3 seconds to exit gracefully
            _, still_alive = psutil.wait_procs(children + [parent], timeout=3)

            # Force-kill anything that ignored the terminate signal
            for p in still_alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass

            print("✓ Ollama process tree stopped")
        except psutil.NoSuchProcess:
            pass  # Already gone
        except Exception as e:
            print(f"Error killing Ollama process tree: {e}")
            # Last resort: use the original subprocess handle
            try:
                proc.kill()
            except Exception:
                pass

    def closeEvent(self, event):
        """Clean up"""
        # Flush any pending debounced save immediately so no data is lost
        self._save_timer.stop()
        self.save_sessions()

        # Persist settings to disk
        self.save_settings_to_disk()

        # Stop all timers
        self._cursor_timer.stop()
        self._scroll_timer.stop()
        self._search_debounce_timer.stop()
        self._scroll_check_timer.stop()
        self._thinking_timer.stop()

        # Stop resource timer
        if hasattr(self, 'resource_timer'):
            self.resource_timer.stop()

        # Stop worker thread
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)

        # Stop Ollama server if we started it — kill the full process tree so
        # child runner processes do not linger in Task Manager
        if self.ollama_process:
            print("Stopping Ollama server...")
            self._kill_process_tree(self.ollama_process)
            self.ollama_process = None

        event.accept()

    def resizeEvent(self, event):
        """Handle window resize to reposition scroll-to-bottom button"""
        super().resizeEvent(event)
        # Reposition the scroll-to-bottom button
        if hasattr(self, 'scroll_bottom_btn') and self.scroll_bottom_btn.isVisible():
            self.position_scroll_button()

    def start_ollama(self):
        """Attempt to start Ollama server"""
        try:
            # First check if Ollama is already running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                print("✓ Ollama is already running")
                return
            except:
                pass

            # Try to start Ollama
            print("Starting Ollama server...")

            if sys.platform == "win32":
                # Windows
                try:
                    # Try to find Ollama in common locations
                    ollama_paths = [
                        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                        r"C:\Program Files\Ollama\ollama.exe",
                        "ollama.exe"  # If in PATH
                    ]

                    for ollama_path in ollama_paths:
                        if os.path.exists(ollama_path) or ollama_path == "ollama.exe":
                            # Start Ollama in background
                            self.ollama_process = subprocess.Popen(
                                [ollama_path if ollama_path != "ollama.exe" else "ollama", "serve"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            atexit.register(self._kill_process_tree, self.ollama_process)
                            print("✓ Ollama started successfully")
                            return
                except Exception as e:
                    print(f"Failed to start Ollama on Windows: {e}")

            elif sys.platform == "darwin":
                # macOS
                try:
                    self.ollama_process = subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    atexit.register(self._kill_process_tree, self.ollama_process)
                    print("✓ Ollama started successfully")
                    return
                except Exception as e:
                    print(f"Failed to start Ollama on macOS: {e}")

            else:
                # Linux
                try:
                    self.ollama_process = subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    atexit.register(self._kill_process_tree, self.ollama_process)
                    print("✓ Ollama started successfully")
                    return
                except Exception as e:
                    print(f"Failed to start Ollama on Linux: {e}")

            print("⚠ Could not auto-start Ollama. Please start it manually.")

        except Exception as e:
            print(f"Error starting Ollama: {e}")

    def save_sessions(self):
        """Save all chat sessions to file"""
        try:
            data = {
                'sessions': self.chat_sessions,
                'current_index': self.current_session_index,
                'saved_at': datetime.now().isoformat()
            }

            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✓ Saved {len(self.chat_sessions)} sessions")
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def load_saved_sessions(self):
        """Load chat sessions from file"""
        try:
            if not self.sessions_file.exists():
                print("No saved sessions found")
                return

            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.chat_sessions = data.get('sessions', [])
            saved_index = data.get('current_index', -1)

            # Populate chat list
            for session in self.chat_sessions:
                item = QListWidgetItem(f"{session['name']}\n{session['timestamp']}")
                self.chat_list.addItem(item)

            # Re-apply theme directly after restoring sessions so colours are
            # correct from the start without an unnecessary fade animation.
            self._do_apply_theme()

            print(f"✓ Loaded {len(self.chat_sessions)} sessions")

        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.chat_sessions = []

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        toggle_sidebar_action = QAction(self)
        toggle_sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        self.addAction(toggle_sidebar_action)

        save_action = QAction(self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_chat)
        self.addAction(save_action)

        new_chat_action = QAction(self)
        new_chat_action.setShortcut(QKeySequence("Ctrl+N"))
        new_chat_action.triggered.connect(self.create_new_session)
        self.addAction(new_chat_action)

        clear_action = QAction(self)
        clear_action.setShortcut(QKeySequence("Ctrl+K"))
        clear_action.triggered.connect(self.clear_chat)
        self.addAction(clear_action)

        settings_action = QAction(self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

        # Search shortcut
        search_action = QAction(self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self.toggle_search)
        self.addAction(search_action)

        # Delete chat session shortcut
        delete_session_action = QAction(self)
        delete_session_action.setShortcut(QKeySequence("Delete"))
        delete_session_action.triggered.connect(self.delete_session_with_key)
        self.addAction(delete_session_action)