"""
Main window for the Ollama Chatbot GUI
"""

import json
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QComboBox, QScrollArea,
                             QLabel, QFrame, QListWidget, QListWidgetItem,
                             QFileDialog, QMessageBox, QInputDialog, QLineEdit,
                             QMenu, QGraphicsOpacityEffect, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction

from gui.widgets import MessageBubble, AnimatedSidebar
from gui.dialogs import SettingsDialog, ModelDownloadDialog
from workers.ollama_worker import OllamaWorker


class ChatbotGUI(QMainWindow):
    """Main application window for the Ollama chatbot"""

    def __init__(self):
        super().__init__()
        self.messages = []
        self.current_response = ""
        self.worker = None
        self.dark_mode = False
        self.sidebar_open = False
        self.chat_sessions = []
        self.current_session_index = -1
        self.shown_no_models_warning = False

        self.settings = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'system_prompt': "You are a helpful AI assistant."
        }

        self.init_ui()
        QTimer.singleShot(100, self.load_models)
        self.create_new_session()

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

        self.toggle_sidebar_btn = QPushButton("☰")
        self.toggle_sidebar_btn.setFixedSize(40, 40)
        self.toggle_sidebar_btn.setObjectName("circularBtn")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        self.model_label = QLabel("Model: None")
        self.model_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setObjectName("circularBtn")
        settings_btn.clicked.connect(self.open_settings)

        theme_btn = QPushButton("🌙")
        theme_btn.setFixedSize(40, 40)
        theme_btn.setObjectName("circularBtn")
        theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn = theme_btn

        top_bar.addWidget(self.toggle_sidebar_btn)
        top_bar.addWidget(self.model_label)
        top_bar.addStretch()
        top_bar.addWidget(settings_btn)
        top_bar.addWidget(theme_btn)

        parent_layout.addLayout(top_bar)

    def setup_chat_area(self, parent_layout):
        """Setup the chat display"""
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)

        self.loading_label = QLabel("⏳ Thinking...")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #6c757d; font-style: italic;")

        parent_layout.addWidget(self.scroll)
        parent_layout.addWidget(self.loading_label)

    def setup_input_area(self, parent_layout):
        """Setup the input area"""
        input_layout = QHBoxLayout()

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your message... (Enter to send, Shift+Enter for new line)")
        self.input_box.setMaximumHeight(100)
        self.input_box.setStyleSheet("border-radius: 20px; padding: 12px; font-size: 14px;")
        self.input_box.installEventFilter(self)

        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setFixedSize(100, 60)
        self.send_btn.setStyleSheet("border-radius: 20px; font-size: 14px;")
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)

        parent_layout.addLayout(input_layout)

    def setup_sidebar(self):
        """Setup the sidebar"""
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("💬 Chats")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        new_chat_btn = QPushButton("➕ New Chat")
        new_chat_btn.clicked.connect(self.create_new_session)
        new_chat_btn.setStyleSheet("padding: 12px; font-weight: bold; border-radius: 20px;")
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

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(35, 35)
        refresh_btn.setStyleSheet("border-radius: 17px; font-size: 14px;")
        refresh_btn.clicked.connect(self.load_models)

        model_layout.addWidget(self.model_selector, 1)
        model_layout.addWidget(refresh_btn)
        layout.addLayout(model_layout)

        download_btn = QPushButton("📥 Download Model")
        download_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                border-radius: 18px;
                font-weight: bold;
                background-color: #28a745;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        download_btn.clicked.connect(self.open_download_dialog)
        layout.addWidget(download_btn)

        delete_btn = QPushButton("🗑️ Delete Model")
        delete_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                border-radius: 18px;
                font-weight: bold;
                background-color: #dc3545;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        delete_btn.clicked.connect(self.delete_model)
        layout.addWidget(delete_btn)

        actions_label = QLabel("📁 Actions")
        actions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(actions_label)

        action_style = "padding: 10px; border-radius: 18px; text-align: left; font-size: 13px;"

        save_btn = QPushButton("💾  Save Chat")
        save_btn.setStyleSheet(action_style)
        save_btn.clicked.connect(self.save_chat)
        layout.addWidget(save_btn)

        load_btn = QPushButton("📂  Load Chat")
        load_btn.setStyleSheet(action_style)
        load_btn.clicked.connect(self.load_chat)
        layout.addWidget(load_btn)

        clear_btn = QPushButton("🗑️  Clear Chat")
        clear_btn.setStyleSheet(action_style)
        clear_btn.clicked.connect(self.clear_chat)
        layout.addWidget(clear_btn)

        layout.addStretch()

    def toggle_sidebar(self):
        """Toggle sidebar"""
        self.sidebar_open = not self.sidebar_open
        animation = QPropertyAnimation(self.sidebar, b"width")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        animation.setStartValue(0 if not self.sidebar_open else 300)
        animation.setEndValue(300 if self.sidebar_open else 0)
        animation.start()
        self.animation = animation

    def toggle_theme(self):
        """Toggle theme"""
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.3)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.3)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def change_theme():
            self.dark_mode = not self.dark_mode
            self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
            self.apply_theme()
            self.fade_in.start()

        self.fade_out.finished.connect(change_theme)
        self.fade_out.start()

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
        self.send_btn.setEnabled(False)
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

        QTimer.singleShot(100, self.scroll_to_bottom)

    def update_response(self, token):
        """Update response"""
        self.current_response += token
        if self.chat_layout.count() > 1:
            last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
            if isinstance(last_widget, MessageBubble) and not last_widget.is_user:
                self.chat_layout.removeWidget(last_widget)
                last_widget.deleteLater()

        bubble = MessageBubble(self.current_response, False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self.scroll_to_bottom)

    def finish_response(self):
        """Finish response"""
        if self.current_response and self.messages[-1]["role"] == "user":
            self.add_message(self.current_response, False)
        self.current_response = ""
        self.input_box.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.loading_label.setVisible(False)
        self.input_box.setFocus()

    def handle_error(self, error):
        """Handle error"""
        QMessageBox.critical(self, "Error", f"Failed: {error}")
        self.finish_response()

    def scroll_to_bottom(self):
        """Scroll to bottom"""
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

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
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def show_chat_context_menu(self, position):
        """Show context menu"""
        item = self.chat_list.itemAt(position)
        if not item:
            return

        menu = QMenu()
        rename_action = QAction("✏️ Rename", self)
        delete_action = QAction("🗑️ Delete", self)

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
        self.clear_chat_display()
        self.messages.clear()
        if self.current_session_index >= 0:
            self.chat_sessions[self.current_session_index]['messages'] = []

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
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
        event.accept()


LIGHT_THEME = """
    QMainWindow, QWidget { background-color: #f8f9fa; color: #212529; }
    QTextEdit { background-color: #ffffff; color: #212529; border: 1px solid #dee2e6; 
                border-radius: 12px; padding: 8px; font-size: 14px; }
    QPushButton { background-color: #007AFF; color: white; border: none; 
                  border-radius: 20px; padding: 10px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
    QComboBox, QListWidget { background-color: #ffffff; border: 1px solid #dee2e6; 
                            border-radius: 10px; padding: 8px; }
    QListWidget::item { padding: 10px; border-radius: 10px; margin: 2px; }
    QListWidget::item:selected { background-color: #007AFF; color: white; }
    AnimatedSidebar { background-color: #ffffff; border-right: 1px solid #dee2e6; }
"""

DARK_THEME = """
    QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; }
    QTextEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #404040; 
                border-radius: 12px; padding: 8px; font-size: 14px; }
    QPushButton { background-color: #007AFF; color: white; border: none; 
                  border-radius: 20px; padding: 10px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
    QComboBox, QListWidget { background-color: #2d2d2d; color: #ffffff; border: 1px solid #404040; 
                            border-radius: 10px; padding: 8px; }
    QListWidget::item { padding: 10px; border-radius: 10px; margin: 2px; }
    QListWidget::item:selected { background-color: #007AFF; }
    AnimatedSidebar { background-color: #252525; border-right: 1px solid #404040; }
"""