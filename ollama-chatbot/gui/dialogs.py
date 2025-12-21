"""
Dialog windows for settings and model management
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QTextEdit, QDialogButtonBox, QLineEdit,
                             QPushButton, QMessageBox)
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
            QDialog, QLabel, QLineEdit {
                font-family: 'Inter', 'Segoe UI', 'Arial', sans-serif;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)

        # Title
        title = QLabel("📥 Download Ollama Model")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Model name input
        input_label = QLabel("Enter model name (e.g., llama3.2, mistral, codellama):")
        layout.addWidget(input_label)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("llama3.2")
        layout.addWidget(self.model_input)

        # Popular models suggestion
        suggestion = QLabel("💡 Popular: llama3.2, mistral, codellama, gemma2, phi3")
        suggestion.setStyleSheet("color: #6c757d; font-size: 12px; font-style: italic;")
        layout.addWidget(suggestion)

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

    def start_download(self):
        """Start downloading the model"""
        from workers.ollama_worker import ModelDownloadWorker

        model_name = self.model_input.text().strip()
        if not model_name:
            QMessageBox.warning(self, "Error", "Please enter a model name!")
            return

        self.download_btn.setEnabled(False)
        self.model_input.setEnabled(False)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Starting download...")

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
        self.model_input.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to download model: {error}")

    def cancel_download(self):
        """Cancel the download"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.reject()