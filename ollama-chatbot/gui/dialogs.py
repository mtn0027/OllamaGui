"""
Dialog windows for settings and model management
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QTextEdit, QDialogButtonBox, QLineEdit,
                             QPushButton, QMessageBox, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Dialog for configuring chat settings"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the settings dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QDialog, QLabel, QTextEdit {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
            }
            QLineEdit {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)

        # Temperature slider
        temp_label = QLabel(f"Temperature: {self.settings['temperature']:.1f}")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(20)
        self.temp_slider.setValue(int(self.settings['temperature'] * 10))
        self.temp_slider.valueChanged.connect(
            lambda v: temp_label.setText(f"Temperature: {v/10:.1f}")
        )

        # Max tokens slider
        tokens_label = QLabel(f"Max Tokens: {self.settings['max_tokens']}")
        self.tokens_slider = QSlider(Qt.Orientation.Horizontal)
        self.tokens_slider.setMinimum(100)
        self.tokens_slider.setMaximum(4000)
        self.tokens_slider.setValue(self.settings['max_tokens'])
        self.tokens_slider.valueChanged.connect(
            lambda v: tokens_label.setText(f"Max Tokens: {v}")
        )

        # System prompt
        system_label = QLabel("System Prompt:")
        self.system_input = QTextEdit()
        self.system_input.setPlainText(self.settings['system_prompt'])
        self.system_input.setMaximumHeight(100)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)

        # Add widgets
        layout.addWidget(temp_label)
        layout.addWidget(self.temp_slider)
        layout.addWidget(tokens_label)
        layout.addWidget(self.tokens_slider)
        layout.addWidget(system_label)
        layout.addWidget(self.system_input)
        layout.addWidget(buttons)

    def save_settings(self):
        """Save the settings and close dialog"""
        self.settings['temperature'] = self.temp_slider.value() / 10
        self.settings['max_tokens'] = self.tokens_slider.value()
        self.settings['system_prompt'] = self.system_input.toPlainText()
        self.accept()


class ModelDownloadDialog(QDialog):
    """Dialog for downloading Ollama models"""

    # Popular Ollama models
    POPULAR_MODELS = [
        ("Llama 3.2 3B", "llama3.2"),
        ("Llama 3.2 1B", "llama3.2:1b"),
        ("Llama 3.1 8B", "llama3.1"),
        ("Llama 3.1 70B", "llama3.1:70b"),
        ("Mistral 7B", "mistral"),
        ("Mistral Nemo 12B", "mistral-nemo"),
        ("Phi-3 Mini", "phi3"),
        ("Phi-3 Medium", "phi3:medium"),
        ("Gemma 2 9B", "gemma2"),
        ("Gemma 2 27B", "gemma2:27b"),
        ("Qwen 2.5 7B", "qwen2.5"),
        ("Code Llama 7B", "codellama"),
        ("Code Llama 13B", "codellama:13b"),
        ("Deepseek Coder 6.7B", "deepseek-coder"),
        ("Vicuna 7B", "vicuna"),
        ("Neural Chat 7B", "neural-chat"),
        ("Starling 7B", "starling-lm"),
        ("-- Custom Model --", "custom")
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Model")
        self.setModal(True)
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize the download dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.setStyleSheet("""
            QDialog, QLabel, QLineEdit, QComboBox {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)

        # Title
        title = QLabel("📥 Download Ollama Model")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Model selection dropdown
        select_label = QLabel("Select a model to download:")
        layout.addWidget(select_label)

        self.model_dropdown = QComboBox()
        for display_name, model_name in self.POPULAR_MODELS:
            self.model_dropdown.addItem(display_name, model_name)
        self.model_dropdown.currentIndexChanged.connect(self.on_model_changed)
        layout.addWidget(self.model_dropdown)

        # Custom input (hidden by default)
        self.custom_label = QLabel("Enter custom model name:")
        self.custom_label.setVisible(False)
        layout.addWidget(self.custom_label)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("e.g., llama3.2, mistral:7b-instruct")
        self.model_input.setVisible(False)
        layout.addWidget(self.model_input)

        # Info label
        info = QLabel("ℹ️ Model size and download time vary. Large models (70B+) may take significant time and disk space.")
        info.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #007AFF; font-weight: bold;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                padding: 10px 20px;
                border-radius: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 18px;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)

        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def on_model_changed(self, index):
        """Handle model selection change"""
        model_data = self.model_dropdown.itemData(index)

        # Show custom input if "custom" is selected
        if model_data == "custom":
            self.custom_label.setVisible(True)
            self.model_input.setVisible(True)
            self.model_input.setFocus()
        else:
            self.custom_label.setVisible(False)
            self.model_input.setVisible(False)

    def start_download(self):
        """Start downloading the model"""
        from workers.ollama_worker import ModelDownloadWorker

        # Get the selected model
        current_data = self.model_dropdown.currentData()

        if current_data == "custom":
            model_name = self.model_input.text().strip()
            if not model_name:
                QMessageBox.warning(self, "Error", "Please enter a model name!")
                return
        else:
            model_name = current_data

        self.download_btn.setEnabled(False)
        self.model_dropdown.setEnabled(False)
        self.model_input.setEnabled(False)
        self.progress_label.setVisible(True)
        self.progress_label.setText(f"Starting download of {model_name}...")

        self.worker = ModelDownloadWorker(model_name)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)
        self.worker.start()

    def update_progress(self, message):
        """Update the progress label"""
        self.progress_label.setText(message)

    def download_finished(self):
        """Handle successful download"""
        self.progress_label.setText("✅ Download complete!")
        self.progress_label.setStyleSheet("color: #28a745; font-weight: bold;")
        QMessageBox.information(self, "Success", "Model downloaded successfully!")
        self.accept()

    def download_error(self, error):
        """Handle download error"""
        self.progress_label.setText(f"❌ Error: {error}")
        self.progress_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.download_btn.setEnabled(True)
        self.model_dropdown.setEnabled(True)
        self.model_input.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to download model: {error}")

    def cancel_download(self):
        """Cancel the download"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.reject()