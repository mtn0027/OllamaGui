"""
Main window for the Ollama Chatbot GUI
"""

import json
import requests
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QComboBox, QScrollArea,
                             QLabel, QFrame, QListWidget, QListWidgetItem,
                             QFileDialog, QMessageBox, QInputDialog, QLineEdit,
                             QMenu, QGraphicsOpacityEffect, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut

from gui.widgets import MessageBubble, AnimatedSidebar
from gui.dialogs import SettingsDialog, ModelDownloadDialog
from workers.ollama_worker import OllamaWorker


class ChatbotGUI(QMainWindow):
    """Main application window for the Ollama chatbot"""

    def __init__(self):
        super().__init__()

        # Setup data directory
        self.data_dir = Path.home() / ".ollama_chatbot"
        self.data_dir.mkdir(exist_ok=True)
        self.sessions_file = self.data_dir / "chat_sessions.json"

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

        self.settings = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt': "You are a helpful AI assistant."
        }

        # Try to start Ollama
        self.start_ollama()

        self.init_ui()

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
        self.setup_chat_area(content_layout)
        self.setup_input_area(content_layout)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_widget)

        self.opacity_effect = QGraphicsOpacityEffect()
        central.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.apply_theme()

    def setup_top_bar(self, parent_layout):
        """Setup the top bar"""
        top_bar = QHBoxLayout()

        self.toggle_sidebar_btn = QPushButton()
        self.toggle_sidebar_btn.setIcon(self.load_icon("menu.svg"))
        self.toggle_sidebar_btn.setIconSize(QSize(20, 20))
        self.toggle_sidebar_btn.setFixedSize(45, 45)
        self.toggle_sidebar_btn.setObjectName("circularBtn")
        self.toggle_sidebar_btn.setToolTip("Toggle Sidebar (Ctrl+B)")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        self.model_label = QLabel("Model: None")
        self.model_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-left: 10px;")

        settings_btn = QPushButton()
        settings_btn.setIcon(self.load_icon("settings.svg"))
        settings_btn.setIconSize(QSize(20, 20))
        settings_btn.setFixedSize(45, 45)
        settings_btn.setObjectName("circularBtn")
        settings_btn.setToolTip("Settings (Ctrl+,)")
        settings_btn.clicked.connect(self.open_settings)

        self.theme_btn = QPushButton()
        self.theme_btn.setIcon(self.load_icon("moon.svg"))
        self.theme_btn.setIconSize(QSize(20, 20))
        self.theme_btn.setFixedSize(45, 45)
        self.theme_btn.setObjectName("circularBtn")
        self.theme_btn.setToolTip("Toggle Dark/Light Theme (Ctrl+T)")
        self.theme_btn.clicked.connect(self.toggle_theme)

        top_bar.addWidget(self.toggle_sidebar_btn)
        top_bar.addWidget(self.model_label)
        top_bar.addStretch()
        top_bar.addWidget(settings_btn)
        top_bar.addWidget(self.theme_btn)

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
        self.scroll_bottom_btn.setFixedSize(50, 50)
        self.scroll_bottom_btn.setToolTip("Scroll to bottom")
        self.scroll_bottom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scroll_bottom_btn.clicked.connect(self.scroll_to_bottom)
        self.scroll_bottom_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.scroll_bottom_btn.raise_()  # Bring to front
        self.scroll_bottom_btn.hide()  # Hidden by default

        # Connect scroll bar to check if we should show the button
        self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        self.loading_label = QLabel("⏳ Thinking...")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #6c757d; font-style: italic;")

        parent_layout.addWidget(chat_wrapper)
        parent_layout.addWidget(self.loading_label)

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
        input_layout = QHBoxLayout()

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self.input_box.setMaximumHeight(100)
        self.input_box.setStyleSheet("border-radius: 20px; padding: 12px; font-size: 14px;")
        self.input_box.installEventFilter(self)

        self.send_btn = QPushButton("Send  ")
        self.send_btn.setIcon(self.load_icon("send.svg"))
        self.send_btn.setIconSize(QSize(18, 18))
        self.send_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Icon on right
        self.send_btn.setFixedSize(100, 60)
        self.send_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.send_btn.setToolTip("Send Message")
        self.send_btn.clicked.connect(self.send_message)

        # Stop button (hidden by default)
        self.stop_btn = QPushButton("Stop  ")
        self.stop_btn.setIcon(self.load_icon("stop.svg"))
        self.stop_btn.setIconSize(QSize(18, 18))
        self.stop_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Icon on right
        self.stop_btn.setFixedSize(100, 60)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                background-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
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
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        new_chat_btn = QPushButton("  New Chat")
        new_chat_btn.setIcon(self.load_icon("plus.svg"))
        new_chat_btn.setIconSize(QSize(16, 16))
        new_chat_btn.clicked.connect(self.create_new_session)
        new_chat_btn.setStyleSheet("padding: 12px; font-weight: bold; border-radius: 20px;")
        new_chat_btn.setToolTip("New Chat (Ctrl+N)")
        layout.addWidget(new_chat_btn)

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_session)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_context_menu)
        self.chat_list.itemDoubleClicked.connect(self.rename_session)
        layout.addWidget(self.chat_list)

        hint_label = QLabel("💡 Right-click chats for options")
        hint_label.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic; padding: 5px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        model_label = QLabel("🤖 Model")
        model_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(model_label)

        self.model_status_label = QLabel("")
        self.model_status_label.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic;")
        self.model_status_label.setVisible(False)
        layout.addWidget(self.model_status_label)

        model_layout = QHBoxLayout()
        self.model_selector = QComboBox()
        self.model_selector.setMinimumHeight(35)
        self.model_selector.currentTextChanged.connect(self.update_model_label)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(self.load_icon("refresh.svg"))
        refresh_btn.setIconSize(QSize(20, 20))
        refresh_btn.setFixedSize(38, 38)
        refresh_btn.setStyleSheet("""
            QPushButton {
                border-radius: 19px;
            }
        """)
        refresh_btn.setToolTip("Refresh Models List")
        refresh_btn.clicked.connect(self.load_models)

        model_layout.addWidget(self.model_selector, 1)
        model_layout.addWidget(refresh_btn)
        layout.addLayout(model_layout)

        download_btn = QPushButton("  Download Model")
        download_btn.setIcon(self.load_icon("download.svg"))
        download_btn.setIconSize(QSize(16, 16))
        download_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                background-color: #28a745;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        download_btn.setToolTip("Download a New Model from Ollama")
        download_btn.clicked.connect(self.open_download_dialog)
        layout.addWidget(download_btn)

        delete_btn = QPushButton("  Delete Model")
        delete_btn.setIcon(self.load_icon("trash.svg"))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                background-color: #dc3545;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        delete_btn.setToolTip("Delete Selected Model")
        delete_btn.clicked.connect(self.delete_model)
        layout.addWidget(delete_btn)

        actions_label = QLabel("📁 Actions")
        actions_label.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 13px;")
        layout.addWidget(actions_label)

        action_style = """
            QPushButton {
                padding: 10px 15px;
                border-radius: 18px;
                text-align: left;
                font-size: 13px;
            }
        """

        save_btn = QPushButton("  Save Chat")
        save_btn.setIcon(self.load_icon("save.svg"))
        save_btn.setIconSize(QSize(16, 16))
        save_btn.setStyleSheet(action_style)
        save_btn.setToolTip("Save Chat to File (Ctrl+S)")
        save_btn.clicked.connect(self.save_chat)
        layout.addWidget(save_btn)

        load_btn = QPushButton("  Load Chat")
        load_btn.setIcon(self.load_icon("folder.svg"))
        load_btn.setIconSize(QSize(16, 16))
        load_btn.setStyleSheet(action_style)
        load_btn.setToolTip("Load Chat from File (Ctrl+O)")
        load_btn.clicked.connect(self.load_chat)
        layout.addWidget(load_btn)

        clear_btn = QPushButton("  Clear Chat")
        clear_btn.setIcon(self.load_icon("trash.svg"))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setStyleSheet(action_style)
        clear_btn.setToolTip("Clear Current Chat (Ctrl+K)")
        clear_btn.clicked.connect(self.clear_chat)
        layout.addWidget(clear_btn)

        layout.addStretch()

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

    def toggle_theme(self):
        """Toggle theme"""
        # Fade out
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.3)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Fade in
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.3)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def change_theme():
            self.dark_mode = not self.dark_mode
            if self.dark_mode:
                self.theme_btn.setIcon(self.load_icon("sun.svg"))
            else:
                self.theme_btn.setIcon(self.load_icon("moon.svg"))
            self.apply_theme()
            fade_in.start()

        fade_out.finished.connect(change_theme)
        fade_out.start()

        # Store references to prevent garbage collection
        self.fade_out_anim = fade_out
        self.fade_in_anim = fade_in

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

        self.add_message(text, True)
        self.input_box.clear()
        self.input_box.setEnabled(False)
        self.send_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.loading_label.setVisible(True)

        self.current_response = ""
        self.worker = OllamaWorker(
            self.model_selector.currentText(),
            text,
            self.settings['system_prompt'],
            self.settings['temperature'],
            self.settings['max_tokens']
        )
        self.worker.token_received.connect(self.update_response)
        self.worker.finished.connect(self.finish_response)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def add_message(self, text, is_user):
        """Add message"""
        bubble = MessageBubble(text, is_user)

        # Connect delete signal for ALL messages (user and AI)
        bubble.delete_requested.connect(self.delete_message)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.messages.append({"role": "user" if is_user else "assistant", "content": text})

        if self.current_session_index >= 0:
            self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
            if len(self.messages) == 1:
                preview = text[:30] + "..." if len(text) > 30 else text
                self.chat_sessions[self.current_session_index]['name'] = preview
                item = self.chat_list.item(self.current_session_index)
                if item:
                    item.setText(f"{preview}\n{self.chat_sessions[self.current_session_index]['timestamp']}")

            # Auto-save after adding message
            self.save_sessions()

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
        """Update response"""
        self.current_response += token
        if self.chat_layout.count() > 1:
            last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
            if isinstance(last_widget, MessageBubble) and not last_widget.is_user:
                self.chat_layout.removeWidget(last_widget)
                last_widget.deleteLater()

        bubble = MessageBubble(self.current_response, False)
        bubble.delete_requested.connect(self.delete_message)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self.scroll_to_bottom)

    def finish_response(self):
        """Finish response"""
        # Don't call add_message again - the bubble is already displayed from update_response
        # Just add to messages list and update session
        if self.current_response and len(self.messages) > 0 and self.messages[-1]["role"] == "user":
            self.messages.append({"role": "assistant", "content": self.current_response})

            # Update session
            if self.current_session_index >= 0:
                self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
                # Auto-save
                self.save_sessions()

        self.current_response = ""
        self.input_box.setEnabled(True)
        self.send_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.loading_label.setVisible(False)
        self.input_box.setFocus()

    def stop_generation(self):
        """Stop the AI generation"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

            # Add partial response if any
            if self.current_response:
                if len(self.messages) > 0 and self.messages[-1]["role"] == "user":
                    self.messages.append({"role": "assistant", "content": self.current_response + " [Stopped]"})

                    # Update the last bubble to show it was stopped
                    if self.chat_layout.count() > 1:
                        last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
                        if isinstance(last_widget, MessageBubble) and not last_widget.is_user:
                            self.chat_layout.removeWidget(last_widget)
                            last_widget.deleteLater()

                    bubble = MessageBubble(self.current_response + "\n\n[Generation stopped by user]", False)
                    bubble.delete_requested.connect(self.delete_message)
                    self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

                    # Update session
                    if self.current_session_index >= 0:
                        self.chat_sessions[self.current_session_index]['messages'] = self.messages.copy()
                        # Auto-save
                        self.save_sessions()

            self.current_response = ""
            self.input_box.setEnabled(True)
            self.send_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.loading_label.setVisible(False)
            self.loading_label.setText("⏹ Generation stopped")
            QTimer.singleShot(2000, lambda: self.loading_label.setText("⏳ Thinking..."))
            self.input_box.setFocus()

    def handle_error(self, error):
        """Handle error"""
        QMessageBox.critical(self, "Error", f"Failed: {error}")
        self.current_response = ""
        self.input_box.setEnabled(True)
        self.send_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.loading_label.setVisible(False)
        self.input_box.setFocus()

    def scroll_to_bottom(self):
        """Scroll to bottom"""
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        self.scroll_bottom_btn.hide()  # Hide button after scrolling

    def apply_theme(self):
        """Apply theme"""
        if self.dark_mode:
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

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
        if self.current_session_index >= 0:
            self.chat_sessions[self.current_session_index]['model'] = model

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
        for msg in self.messages:
            bubble = MessageBubble(msg['content'], msg['role'] == 'user')
            bubble.delete_requested.connect(self.delete_message)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

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
        """Clear display"""
        for i in reversed(range(self.chat_layout.count() - 1)):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

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
                            f.write(f"{role}\n{msg['content']}\n\n---\n\n")
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

                QMessageBox.information(self, "Success", "Loaded!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def open_settings(self):
        """Open settings"""
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()

    def closeEvent(self, event):
        """Clean up"""
        # Save sessions before closing
        self.save_sessions()

        # Stop worker thread
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)

        # Stop Ollama server if we started it
        if self.ollama_process:
            try:
                print("Stopping Ollama server...")
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=5)
                print("✓ Ollama server stopped")
            except Exception as e:
                print(f"Error stopping Ollama: {e}")
                try:
                    self.ollama_process.kill()
                except:
                    pass

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

            print(f"✓ Loaded {len(self.chat_sessions)} sessions")

        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.chat_sessions = []


LIGHT_THEME = """
    QMainWindow, QWidget { background-color: #f8f9fa; color: #212529; }
    QTextEdit { background-color: #ffffff; color: #212529; border: 1px solid #dee2e6; 
                border-radius: 12px; padding: 8px; font-size: 14px; }
    QPushButton { background-color: #007AFF; color: white; border: none; 
                  border-radius: 15px; padding: 10px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
    QComboBox, QListWidget { background-color: #ffffff; border: 1px solid #dee2e6; 
                            border-radius: 10px; padding: 8px; }
    QListWidget::item { padding: 10px; border-radius: 10px; margin: 2px; }
    QListWidget::item:selected { background-color: #007AFF; color: white; }
    AnimatedSidebar { background-color: #ffffff; border-right: 1px solid #dee2e6; }
    
    /* Custom Scrollbar Styling - Light Theme */
    QScrollBar:vertical {
        background: #f8f9fa;
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #c0c0c0;
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a0a0a0;
    }
    QScrollBar::handle:vertical:pressed {
        background: #808080;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    
    QScrollBar:horizontal {
        background: #f8f9fa;
        height: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #c0c0c0;
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #a0a0a0;
    }
    QScrollBar::handle:horizontal:pressed {
        background: #808080;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""

DARK_THEME = """
    QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; }
    QTextEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #404040; 
                border-radius: 12px; padding: 8px; font-size: 14px; }
    QPushButton { background-color: #007AFF; color: white; border: none; 
                  border-radius: 15px; padding: 10px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
    QComboBox, QListWidget { background-color: #2d2d2d; color: #ffffff; border: 1px solid #404040; 
                            border-radius: 10px; padding: 8px; }
    QListWidget::item { padding: 10px; border-radius: 10px; margin: 2px; }
    QListWidget::item:selected { background-color: #007AFF; }
    AnimatedSidebar { background-color: #252525; border-right: 1px solid #404040; }
    
    /* Custom Scrollbar Styling - Dark Theme */
    QScrollBar:vertical {
        background: #1e1e1e;
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #4a4a4a;
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #5a5a5a;
    }
    QScrollBar::handle:vertical:pressed {
        background: #6a6a6a;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    
    QScrollBar:horizontal {
        background: #1e1e1e;
        height: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #4a4a4a;
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #5a5a5a;
    }
    QScrollBar::handle:horizontal:pressed {
        background: #6a6a6a;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""