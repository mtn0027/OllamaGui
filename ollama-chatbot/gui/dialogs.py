"""
Dialog windows for settings and model management
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QTextEdit, QDialogButtonBox, QLineEdit,
                             QPushButton, QMessageBox, QComboBox, QCheckBox,
                             QScrollArea, QWidget, QFrame, QGridLayout, QProgressBar, QGroupBox,
                             QColorDialog)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import psutil
import os


class SettingsDialog(QDialog):
    """Dialog for configuring chat settings"""

    # Preset accent color swatches
    ACCENT_PRESETS = [
        "#007AFF",  # Blue (default)
        "#34C759",  # Green
        "#FF3B30",  # Red
        "#FF9500",  # Orange
        "#AF52DE",  # Purple
        "#FF2D55",  # Pink
        "#5AC8FA",  # Light Blue
        "#FFCC00",  # Yellow
        "#00C7BE",  # Teal
    ]

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.settings = main_window.settings

        # Local working copies of appearance values — only committed on Save
        self._pending_dark_mode = self.settings.get('dark_mode', False)
        self._pending_accent = self.settings.get('accent_color', '#007AFF')

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def setup_ui(self):
        """Initialize the settings dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

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
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCheckBox {
                spacing: 5px;
                padding: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cGF0aCBkPSJNMTAgMkw0LjUgNy41TDIgNSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIi8+Cjwvc3ZnPg==);
            }
            QCheckBox::indicator:hover {
                border-color: #007AFF;
            }
        """)

        # ── Appearance Group ──────────────────────────────────────────
        appearance_group = QGroupBox("🎨 Appearance")
        appearance_layout = QVBoxLayout()
        appearance_layout.setSpacing(12)

        # Dark mode checkbox
        dark_frame = QFrame()
        dark_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        dark_frame_layout = QVBoxLayout(dark_frame)
        dark_frame_layout.setContentsMargins(5, 5, 5, 5)

        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.dark_mode_checkbox.setChecked(self._pending_dark_mode)
        self.dark_mode_checkbox.setToolTip("Toggle dark/light theme (live preview)")
        self.dark_mode_checkbox.toggled.connect(self._on_dark_mode_toggled)

        dark_frame_layout.addWidget(self.dark_mode_checkbox)
        appearance_layout.addWidget(dark_frame)

        # Accent color label
        accent_label = QLabel("Accent Color:")
        accent_label.setStyleSheet("font-weight: bold; padding-left: 2px;")
        appearance_layout.addWidget(accent_label)

        # ── Accent color container frame ─────────────────────────────
        self._accent_frame = QFrame()
        self._accent_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        accent_frame_layout = QVBoxLayout(self._accent_frame)
        accent_frame_layout.setContentsMargins(10, 10, 10, 10)
        accent_frame_layout.setSpacing(10)

        # Swatch grid
        swatch_grid = QGridLayout()
        swatch_grid.setSpacing(8)
        self._swatch_buttons = []

        for idx, color in enumerate(self.ACCENT_PRESETS):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setToolTip(color)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._swatch_style(color, selected=(color.upper() == self._pending_accent.upper())))
            btn.clicked.connect(lambda checked, c=color: self._select_accent(c))
            row, col = divmod(idx, 5)
            swatch_grid.addWidget(btn, row, col)
            self._swatch_buttons.append((btn, color))

        accent_frame_layout.addLayout(swatch_grid)

        # Custom button + preview row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self._custom_btn = QPushButton("Custom…")
        self._custom_btn.setFixedHeight(32)
        self._custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._custom_btn.clicked.connect(self._pick_custom_color)
        self._refresh_custom_btn_style()
        bottom_row.addWidget(self._custom_btn)

        # Color preview pill
        self._accent_preview = QLabel()
        self._accent_preview.setFixedSize(160, 32)
        self._accent_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_preview_label()
        bottom_row.addWidget(self._accent_preview)
        bottom_row.addStretch()

        accent_frame_layout.addLayout(bottom_row)
        appearance_layout.addWidget(self._accent_frame)

        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # ── Display Settings Group ────────────────────────────────────
        display_group = QGroupBox("🖥️ Display Settings")
        display_layout = QVBoxLayout()

        # Add frame around checkbox
        checkbox_frame = QFrame()
        checkbox_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        checkbox_frame_layout = QVBoxLayout(checkbox_frame)
        checkbox_frame_layout.setContentsMargins(5, 5, 5, 5)

        self.show_resources_checkbox = QCheckBox("Show resource usage in top bar")
        self.show_resources_checkbox.setChecked(self.settings.get('show_resources', False))
        self.show_resources_checkbox.setToolTip(
            "Display real-time CPU and RAM usage of the Ollama server.\n"
            "Shows how much resources the AI model is consuming."
        )

        checkbox_frame_layout.addWidget(self.show_resources_checkbox)
        display_layout.addWidget(checkbox_frame)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # ── Model Settings Group ──────────────────────────────────────
        model_group = QGroupBox("⚙️ Model Settings")
        model_layout = QVBoxLayout()

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

        model_layout.addWidget(temp_label)
        model_layout.addWidget(self.temp_slider)
        model_layout.addWidget(tokens_label)
        model_layout.addWidget(self.tokens_slider)
        model_layout.addWidget(system_label)
        model_layout.addWidget(self.system_input)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # ── Dialog buttons ────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self._on_cancel)

        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Appearance helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert a hex color string to an (r, g, b) tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    @staticmethod
    def _darken_hex(hex_color: str, factor: float = 0.40) -> str:
        """Return a darkened version of hex_color by reducing each channel."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        r = max(0, int(int(hex_color[0:2], 16) * (1 - factor)))
        g = max(0, int(int(hex_color[2:4], 16) * (1 - factor)))
        b = max(0, int(int(hex_color[4:6], 16) * (1 - factor)))
        return f"#{r:02X}{g:02X}{b:02X}"

    def _luminance_text_color(self, hex_color: str) -> str:
        """Return '#000000' or '#ffffff' depending on the luminance of hex_color."""
        r, g, b = self._hex_to_rgb(hex_color)
        luminance = r * 0.299 + g * 0.587 + b * 0.114
        return "#000000" if luminance > 128 else "#ffffff"

    def _swatch_style(self, color: str, selected: bool = False) -> str:
        """Return the stylesheet for a swatch button."""
        ring_color = "#ffffff" if self._pending_dark_mode else "#212529"
        hover_color = self._darken_hex(color, 0.40)

        if selected:
            return f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid {ring_color};
                    border-radius: 6px;
                    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.20);
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border: 2px solid {hover_color};
                }}
            """

    def _refresh_custom_btn_style(self):
        """Update the 'Custom…' button style to match the current dark/light mode."""
        text_color = "#ffffff" if self._pending_dark_mode else "#212529"
        bg_color = "rgba(255,255,255,0.08)" if self._pending_dark_mode else "transparent"
        border_color = "#5a5a5a" if self._pending_dark_mode else "#dee2e6"
        hover_border = self._pending_accent

        self._custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                color: {text_color};
            }}
            QPushButton:hover {{
                border-color: {hover_border};
                color: {text_color};
            }}
        """)

    def _update_swatch_selection(self):
        """Refresh swatch button borders to reflect the current pending accent."""
        for btn, color in self._swatch_buttons:
            selected = color.upper() == self._pending_accent.upper()
            btn.setStyleSheet(self._swatch_style(color, selected))

    def _update_preview_label(self):
        """Update the wider pill preview label to show the pending accent."""
        text_color = self._luminance_text_color(self._pending_accent)
        r, g, b = self._hex_to_rgb(self._pending_accent)
        border_color = f"rgba({r}, {g}, {b}, 0.40)"
        self._accent_preview.setStyleSheet(
            f"""
            QLabel {{
                background-color: {self._pending_accent};
                color: {text_color};
                border-radius: 16px;
                border: 1px solid {border_color};
                font-size: 11px;
                font-weight: bold;
            }}
            """
        )
        self._accent_preview.setText(self._pending_accent.upper())

    def _update_accent_frame_border(self):
        """Refresh the accent container frame border for the current theme."""
        border_color = "#404040" if self._pending_dark_mode else "#dee2e6"
        self._accent_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)

    def _select_accent(self, color: str):
        """Handle swatch or custom color selection (pending only)."""
        self._pending_accent = color
        self._update_swatch_selection()
        self._update_preview_label()
        self._refresh_custom_btn_style()

    def _on_dark_mode_toggled(self, checked: bool):
        """Live-preview dark/light mode while the dialog is open."""
        self._pending_dark_mode = checked
        # Temporarily apply so the user can see the effect immediately
        self.main_window.dark_mode = checked
        self.main_window.apply_theme()
        # Refresh accent section visuals to match the new theme
        self._update_swatch_selection()
        self._update_accent_frame_border()
        self._refresh_custom_btn_style()

    def _pick_custom_color(self):
        """Open QColorDialog and apply the chosen color as the pending accent."""
        initial = QColor(self._pending_accent)
        color = QColorDialog.getColor(initial, self, "Choose Accent Color")
        if color.isValid():
            self._select_accent(color.name().upper())

    # ------------------------------------------------------------------
    # Save / Cancel
    # ------------------------------------------------------------------

    def save_settings(self):
        """Commit all values to main_window.settings and close."""
        self.settings['temperature'] = self.temp_slider.value() / 10
        self.settings['max_tokens'] = self.tokens_slider.value()
        self.settings['system_prompt'] = self.system_input.toPlainText()
        self.settings['show_resources'] = self.show_resources_checkbox.isChecked()
        self.settings['dark_mode'] = self._pending_dark_mode
        self.settings['accent_color'] = self._pending_accent

        # Write back to the main window's authoritative attributes
        self.main_window.dark_mode = self._pending_dark_mode
        self.main_window.settings['accent_color'] = self._pending_accent

        # Apply the final theme (accent may have changed)
        self.main_window.apply_theme()

        self.accept()

    def _on_cancel(self):
        """Revert any live-preview changes and close without saving."""
        # Restore the original dark_mode that was in effect before the dialog opened
        original_dark = self.settings.get('dark_mode', False)
        self.main_window.dark_mode = original_dark
        self.main_window.apply_theme()
        self.reject()


class ModelCard(QFrame):
    """Widget for displaying a single model card"""

    clicked = pyqtSignal(dict)  # Signal to emit when clicked

    def __init__(self, model_data, is_dark_theme=False, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.is_dark_theme = is_dark_theme
        self.is_selected = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the model card UI"""
        self.setFrameShape(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # Model name and parameters
        title_layout = QHBoxLayout()
        self.name_label = QLabel(self.model_data['name'])
        self.name_label.setFont(QFont('Inter', 12, QFont.Weight.Bold))
        title_layout.addWidget(self.name_label)

        if self.model_data.get('params'):
            params_badge = QLabel(self.model_data['params'])
            params_badge.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 10px;
                    padding: 3px 10px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            params_badge.setFixedHeight(20)
            title_layout.addWidget(params_badge)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Tags
        if self.model_data.get('tags'):
            tags_layout = QHBoxLayout()
            for tag in self.model_data['tags']:
                tag_label = QLabel(tag)
                if self.is_dark_theme:
                    tag_label.setStyleSheet("""
                        QLabel {
                            background-color: rgba(255, 255, 255, 0.1);
                            color: #c0c0c0;
                            border-radius: 8px;
                            padding: 2px 8px;
                            font-size: 9px;
                        }
                    """)
                else:
                    tag_label.setStyleSheet("""
                        QLabel {
                            background-color: rgba(108, 117, 125, 0.2);
                            color: #495057;
                            border-radius: 8px;
                            padding: 2px 8px;
                            font-size: 9px;
                        }
                    """)
                tag_label.setFixedHeight(18)
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        # Description
        self.desc_label = QLabel(self.model_data.get('description', ''))
        self.desc_label.setWordWrap(True)
        if self.is_dark_theme:
            self.desc_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        else:
            self.desc_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(self.desc_label)

        # Size and RAM info
        info_layout = QHBoxLayout()

        self.size_label = QLabel(f"📦 {self.model_data.get('size', 'N/A')}")
        if self.is_dark_theme:
            self.size_label.setStyleSheet("font-size: 11px; color: #b0b0b0;")
        else:
            self.size_label.setStyleSheet("font-size: 11px; color: #495057;")
        info_layout.addWidget(self.size_label)

        info_layout.addSpacing(15)

        self.ram_label = QLabel(f"💾 {self.model_data.get('ram', 'N/A')} RAM")
        if self.is_dark_theme:
            self.ram_label.setStyleSheet("font-size: 11px; color: #b0b0b0;")
        else:
            self.ram_label.setStyleSheet("font-size: 11px; color: #495057;")
        info_layout.addWidget(self.ram_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Apply initial styling
        self.update_style()

    def update_style(self):
        """Update the card styling based on selection and theme"""
        if self.is_dark_theme:
            if self.is_selected:
                self.setStyleSheet("""
                    ModelCard {
                        background-color: #3d3d3d;
                        border: 3px solid #007AFF;
                        border-radius: 12px;
                    }
                """)
                self.name_label.setStyleSheet("color: #007AFF; font-weight: bold;")
            else:
                self.setStyleSheet("""
                    ModelCard {
                        background-color: #2d2d2d;
                        border: 2px solid #404040;
                        border-radius: 12px;
                    }
                    ModelCard:hover {
                        border: 2px solid #007AFF;
                        background-color: #3d3d3d;
                    }
                """)
                self.name_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        else:
            if self.is_selected:
                self.setStyleSheet("""
                    ModelCard {
                        background-color: #e7f3ff;
                        border: 3px solid #007AFF;
                        border-radius: 12px;
                    }
                """)
                self.name_label.setStyleSheet("color: #007AFF; font-weight: bold;")
            else:
                self.setStyleSheet("""
                    ModelCard {
                        background-color: #ffffff;
                        border: 2px solid #e9ecef;
                        border-radius: 12px;
                    }
                    ModelCard:hover {
                        border: 2px solid #007AFF;
                        background-color: #f8f9fa;
                    }
                """)
                self.name_label.setStyleSheet("color: #212529; font-weight: bold;")

    def set_selected(self, selected):
        """Set the selected state"""
        self.is_selected = selected
        self.update_style()

    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.model_data)
        super().mousePressEvent(event)


class ModelDownloadDialog(QDialog):
    """Dialog for downloading Ollama models with search and details"""

    # Comprehensive model database
    MODELS_DATABASE = [
        {
            'name': 'Llama 3.2 3B',
            'model_id': 'llama3.2',
            'params': '3B',
            'size': '2.0 GB',
            'ram': '8 GB',
            'description': 'Latest Llama model, excellent for general chat and reasoning tasks.',
            'tags': ['💬 Chat', '🎯 General', '🔥 Popular']
        },
        {
            'name': 'Llama 3.2 1B',
            'model_id': 'llama3.2:1b',
            'params': '1B',
            'size': '1.3 GB',
            'ram': '4 GB',
            'description': 'Smallest Llama 3.2, perfect for quick responses on low-end hardware.',
            'tags': ['💬 Chat', '⚡ Fast', '💻 Low RAM']
        },
        {
            'name': 'Llama 3.1 8B',
            'model_id': 'llama3.1',
            'params': '8B',
            'size': '4.7 GB',
            'ram': '16 GB',
            'description': 'Powerful general-purpose model with strong reasoning capabilities.',
            'tags': ['💬 Chat', '🎯 General', '🔥 Popular']
        },
        {
            'name': 'Llama 3.1 70B',
            'model_id': 'llama3.1:70b',
            'params': '70B',
            'size': '40 GB',
            'ram': '64 GB',
            'description': 'Top-tier Llama model for complex tasks and advanced reasoning.',
            'tags': ['💬 Chat', '🧠 Advanced', '🎯 General']
        },
        {
            'name': 'Mistral 7B',
            'model_id': 'mistral',
            'params': '7B',
            'size': '4.1 GB',
            'ram': '16 GB',
            'description': 'High-quality open model with excellent performance across tasks.',
            'tags': ['💬 Chat', '🎯 General', '🔥 Popular']
        },
        {
            'name': 'Mistral Nemo 12B',
            'model_id': 'mistral-nemo',
            'params': '12B',
            'size': '7.0 GB',
            'ram': '24 GB',
            'description': 'Larger Mistral variant with enhanced capabilities.',
            'tags': ['💬 Chat', '🎯 General']
        },
        {
            'name': 'Phi-3 Mini',
            'model_id': 'phi3',
            'params': '3.8B',
            'size': '2.3 GB',
            'ram': '8 GB',
            'description': 'Microsoft\'s compact model, efficient and capable.',
            'tags': ['💬 Chat', '⚡ Fast', '💻 Low RAM']
        },
        {
            'name': 'Phi-3 Medium',
            'model_id': 'phi3:medium',
            'params': '14B',
            'size': '7.9 GB',
            'ram': '24 GB',
            'description': 'Balanced Phi model for various tasks.',
            'tags': ['💬 Chat', '🎯 General']
        },
        {
            'name': 'Gemma 2 9B',
            'model_id': 'gemma2',
            'params': '9B',
            'size': '5.4 GB',
            'ram': '16 GB',
            'description': 'Google\'s latest open model with strong performance.',
            'tags': ['💬 Chat', '🎯 General', '🔥 Popular']
        },
        {
            'name': 'Gemma 2 27B',
            'model_id': 'gemma2:27b',
            'params': '27B',
            'size': '16 GB',
            'ram': '32 GB',
            'description': 'Larger Gemma variant for advanced use cases.',
            'tags': ['💬 Chat', '🧠 Advanced']
        },
        {
            'name': 'Qwen 2.5 7B',
            'model_id': 'qwen2.5',
            'params': '7B',
            'size': '4.4 GB',
            'ram': '16 GB',
            'description': 'Alibaba\'s multilingual model with strong coding abilities.',
            'tags': ['💬 Chat', '💻 Code', '🌍 Multilingual']
        },
        {
            'name': 'Code Llama 7B',
            'model_id': 'codellama',
            'params': '7B',
            'size': '3.8 GB',
            'ram': '16 GB',
            'description': 'Specialized for code generation and programming tasks.',
            'tags': ['💻 Code', '🔥 Popular']
        },
        {
            'name': 'Code Llama 13B',
            'model_id': 'codellama:13b',
            'params': '13B',
            'size': '7.3 GB',
            'ram': '24 GB',
            'description': 'Larger Code Llama for complex programming tasks.',
            'tags': ['💻 Code', '🧠 Advanced']
        },
        {
            'name': 'Deepseek Coder 6.7B',
            'model_id': 'deepseek-coder',
            'params': '6.7B',
            'size': '3.8 GB',
            'ram': '16 GB',
            'description': 'Specialized coding model with excellent code understanding.',
            'tags': ['💻 Code', '🔥 Popular']
        },
        {
            'name': 'Vicuna 7B',
            'model_id': 'vicuna',
            'params': '7B',
            'size': '3.8 GB',
            'ram': '16 GB',
            'description': 'Chat-optimized model trained with human feedback.',
            'tags': ['💬 Chat', '🎯 General']
        },
        {
            'name': 'Neural Chat 7B',
            'model_id': 'neural-chat',
            'params': '7B',
            'size': '4.1 GB',
            'ram': '16 GB',
            'description': 'Intel\'s fine-tuned chat model with strong conversational abilities.',
            'tags': ['💬 Chat']
        },
        {
            'name': 'Starling 7B',
            'model_id': 'starling-lm',
            'params': '7B',
            'size': '4.1 GB',
            'ram': '16 GB',
            'description': 'RLHF-trained model with human-like responses.',
            'tags': ['💬 Chat', '🎯 General']
        },
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Ollama Model")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.worker = None
        self.selected_model = None
        self.filtered_models = self.MODELS_DATABASE.copy()
        self.model_cards = []  # Keep track of all model cards
        self.download_canceled = False  # Track if download was canceled

        # Check if parent has dark mode enabled
        self.is_dark_theme = False
        if parent and hasattr(parent, 'dark_mode'):
            self.is_dark_theme = parent.dark_mode

        self.setup_ui()

    def setup_ui(self):
        """Initialize the enhanced download dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Apply theme-aware styling to the dialog
        if self.is_dark_theme:
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 2px solid #404040;
                }
                QLineEdit:focus {
                    border: 2px solid #007AFF;
                    background-color: #3d3d3d;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #212529;
                }
            """)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📥 Download Ollama Model")
        title.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search models by name, size, or category...")
        self.search_input.textChanged.connect(self.filter_models)
        self.search_input.setFixedHeight(40)

        if self.is_dark_theme:
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px 15px;
                    border-radius: 20px;
                    border: 2px solid #404040;
                    font-size: 14px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLineEdit:focus {
                    border: 2px solid #007AFF;
                    background-color: #3d3d3d;
                }
            """)
        else:
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px 15px;
                    border-radius: 20px;
                    border: 2px solid #dee2e6;
                    font-size: 14px;
                    background-color: #f8f9fa;
                    color: #212529;
                }
                QLineEdit:focus {
                    border: 2px solid #007AFF;
                    background-color: white;
                }
            """)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Filter buttons
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        filter_layout.addWidget(filter_label)

        filters = [
            ("All", "all"),
            ("Chat", "chat"),
            ("Code", "code"),
            ("Fast", "fast"),
            ("Popular", "popular"),
        ]

        self.filter_buttons = []
        for text, filter_type in filters:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(filter_type == "all")
            btn.clicked.connect(lambda checked, f=filter_type: self.apply_filter(f))

            if self.is_dark_theme:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 6px 15px;
                        border-radius: 15px;
                        border: 2px solid #404040;
                        background-color: #2d2d2d;
                        color: #ffffff;
                        font-size: 11px;
                    }
                    QPushButton:checked {
                        background-color: #007AFF;
                        color: white;
                        border: 2px solid #007AFF;
                    }
                    QPushButton:hover {
                        border: 2px solid #007AFF;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 6px 15px;
                        border-radius: 15px;
                        border: 2px solid #dee2e6;
                        background-color: white;
                        color: #212529;
                        font-size: 11px;
                    }
                    QPushButton:checked {
                        background-color: #007AFF;
                        color: white;
                        border: 2px solid #007AFF;
                    }
                    QPushButton:hover {
                        border: 2px solid #007AFF;
                    }
                """)
            self.filter_buttons.append((btn, filter_type))
            filter_layout.addWidget(btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Scrollable model list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        if self.is_dark_theme:
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: #252525;
                    border-radius: 10px;
                }
            """)
        else:
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                }
            """)

        scroll_widget = QWidget()
        self.models_layout = QVBoxLayout(scroll_widget)
        self.models_layout.setSpacing(10)
        self.models_layout.setContentsMargins(10, 10, 10, 10)

        # Populate models
        self.populate_models()

        self.models_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Selected model info
        self.selection_frame = QFrame()
        if self.is_dark_theme:
            self.selection_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 122, 255, 0.2);
                    border: 2px solid #007AFF;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
        else:
            self.selection_frame.setStyleSheet("""
                QFrame {
                    background-color: #e7f3ff;
                    border: 2px solid #007AFF;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
        self.selection_frame.setVisible(False)

        selection_layout = QHBoxLayout(self.selection_frame)
        self.selection_label = QLabel("No model selected")
        self.selection_label.setStyleSheet("font-weight: bold; color: #007AFF;")
        selection_layout.addWidget(self.selection_label)
        selection_layout.addStretch()

        layout.addWidget(self.selection_frame)

        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #007AFF; font-weight: bold;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setTextVisible(True)

        if self.is_dark_theme:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #007AFF;
                    border-radius: 12px;
                    text-align: center;
                    background-color: #2d2d2d;
                    color: #ffffff;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #007AFF;
                    border-radius: 10px;
                }
            """)
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #007AFF;
                    border-radius: 12px;
                    text-align: center;
                    background-color: #f0f0f0;
                    color: #212529;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #007AFF;
                    border-radius: 10px;
                }
            """)

        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Custom model input section (collapsible)
        custom_frame = QFrame()
        custom_layout = QVBoxLayout(custom_frame)

        custom_toggle = QPushButton("⚙️ Enter Custom Model Name")
        custom_toggle.setCheckable(True)
        custom_toggle.clicked.connect(self.toggle_custom_input)
        custom_toggle.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: none;
                background-color: transparent;
                color: #007AFF;
                font-weight: bold;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        custom_layout.addWidget(custom_toggle)

        self.custom_input_widget = QWidget()
        custom_input_layout = QVBoxLayout(self.custom_input_widget)
        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("e.g., llama3.2, mistral:7b-instruct-q4_0")

        if self.is_dark_theme:
            self.custom_model_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px;
                    border-radius: 8px;
                    border: 2px solid #404040;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
            """)
        else:
            self.custom_model_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px;
                    border-radius: 8px;
                    border: 2px solid #dee2e6;
                    background-color: #ffffff;
                    color: #212529;
                }
            """)
        custom_input_layout.addWidget(self.custom_model_input)
        self.custom_error_label = QLabel("")
        self.custom_error_label.setStyleSheet("color: #dc3545; font-size: 11px; padding-left: 4px;")
        self.custom_error_label.setVisible(False)
        self.custom_error_label.setWordWrap(True)
        custom_input_layout.addWidget(self.custom_error_label)
        self.custom_input_widget.setVisible(False)
        custom_layout.addWidget(self.custom_input_widget)

        layout.addWidget(custom_frame)

        # Buttons
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇️ Download Model")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setFixedHeight(45)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                padding: 10px 30px;
                border-radius: 22px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #0056b3; 
            }
            QPushButton:disabled {
                background-color: #c0c0c0;
            }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 30px;
                border-radius: 22px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #5a6268; 
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def populate_models(self):
        """Populate the models list with cards"""
        # Clear existing
        self.model_cards = []
        while self.models_layout.count() > 1:  # Keep the stretch
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add model cards
        for model in self.filtered_models:
            card = ModelCard(model, self.is_dark_theme)
            card.clicked.connect(self.select_model)  # Connect the signal
            self.models_layout.insertWidget(self.models_layout.count() - 1, card)
            self.model_cards.append(card)

    def filter_models(self):
        """Filter models based on search text"""
        search_text = self.search_input.text().lower()

        self.filtered_models = [
            model for model in self.MODELS_DATABASE
            if search_text in model['name'].lower() or
               search_text in model['description'].lower() or
               search_text in model.get('params', '').lower() or
               any(search_text in tag.lower() for tag in model.get('tags', []))
        ]

        # Clear selection when filtering
        self.selected_model = None
        self.selection_frame.setVisible(False)
        self.download_btn.setEnabled(False)

        self.populate_models()

    def apply_filter(self, filter_type):
        """Apply category filter"""
        # Uncheck other filter buttons
        for btn, ftype in self.filter_buttons:
            if ftype != filter_type:
                btn.setChecked(False)

        # Ensure the clicked button stays checked
        for btn, ftype in self.filter_buttons:
            if ftype == filter_type:
                btn.setChecked(True)

        if filter_type == "all":
            self.filtered_models = self.MODELS_DATABASE.copy()
        else:
            filter_map = {
                "chat": "💬 Chat",
                "code": "💻 Code",
                "fast": "⚡ Fast",
                "popular": "🔥 Popular"
            }
            filter_tag = filter_map.get(filter_type, "")
            self.filtered_models = [
                model for model in self.MODELS_DATABASE
                if any(filter_tag in tag for tag in model.get('tags', []))
            ]

        # Clear selection when changing filter
        self.selected_model = None
        self.selection_frame.setVisible(False)
        self.download_btn.setEnabled(False)

        self.populate_models()

    def select_model(self, model_data):
        """Handle model selection"""
        self.selected_model = model_data

        # Deselect all cards first
        for card in self.model_cards:
            card.set_selected(False)

        # Select the clicked card
        for card in self.model_cards:
            if card.model_data == model_data:
                card.set_selected(True)
                break

        # Show selection info and enable download button
        self.selection_frame.setVisible(True)
        self.selection_label.setText(
            f"✓ Selected: {model_data['name']} ({model_data['size']}) - {model_data['ram']} RAM required"
        )
        self.download_btn.setEnabled(True)

        # Hide custom input if it was visible
        if self.custom_input_widget.isVisible():
            self.custom_input_widget.setVisible(False)

    def toggle_custom_input(self, checked):
        """Toggle custom model input visibility"""
        self.custom_input_widget.setVisible(checked)
        if checked:
            self.custom_model_input.setFocus()
            # Deselect any card selection
            for card in self.model_cards:
                card.set_selected(False)
            self.selected_model = None
            self.selection_frame.setVisible(False)
            self.download_btn.setEnabled(True)  # Enable for custom input
        else:
            # Re-enable download button if a model is selected
            self.download_btn.setEnabled(self.selected_model is not None)

    def _validate_custom_model_name(self, model_name: str) -> bool:
        """Validate a custom model name against the Ollama registry.

        Makes a GET request to the Ollama search API and checks whether the
        base name (the part before an optional ':' tag) appears in the results.
        Shows self.custom_error_label with an appropriate message on failure
        and returns False; hides it and returns True on success.
        """
        import requests as _requests

        base_name = model_name.split(":")[0].lower()
        try:
            resp = _requests.get(
                f"https://ollama.com/api/models?q={base_name}&limit=10",
                timeout=5,
            )
            if resp.status_code == 404:
                self.custom_error_label.setText(
                    f"Model '{model_name}' was not found on the Ollama registry. "
                    "Check the name at ollama.com/library."
                )
                self.custom_error_label.setVisible(True)
                return False
            if resp.status_code != 200:
                self.custom_error_label.setText(
                    "Could not reach ollama.com to verify the model name. "
                    "Check your internet connection."
                )
                self.custom_error_label.setVisible(True)
                return False
            results = resp.json()
        except (_requests.exceptions.ConnectionError, _requests.exceptions.Timeout):
            self.custom_error_label.setText(
                "Could not reach ollama.com to verify the model name. "
                "Check your internet connection."
            )
            self.custom_error_label.setVisible(True)
            return False
        except Exception:
            self.custom_error_label.setText(
                "Could not reach ollama.com to verify the model name. "
                "Check your internet connection."
            )
            self.custom_error_label.setVisible(True)
            return False

        # The API returns a list directly or a dict with a 'models' key —
        # handle both shapes defensively.
        if isinstance(results, list):
            models = results
        else:
            models = results.get("models", [])

        for entry in models:
            entry_name = entry.get("name", "").split(":")[0].lower()
            if entry_name == base_name:
                self.custom_error_label.setVisible(False)
                self.custom_error_label.setText("")
                return True

        self.custom_error_label.setText(
            f"Model '{model_name}' was not found on the Ollama registry. "
            "Check the name at ollama.com/library."
        )
        self.custom_error_label.setVisible(True)
        return False

    def start_download(self):
        """Start downloading the model"""
        import requests
        from workers.ollama_worker import ModelDownloadWorker

        # Check if Ollama is running with improved error handling
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Ollama Not Running",
                "Cannot download model: Ollama server is not running.\n\n"
                "Please start Ollama:\n"
                "• Windows: Launch 'Ollama' from Start Menu\n"
                "• macOS: Open Ollama.app from Applications\n"
                "• Linux: Run 'ollama serve' in terminal\n\n"
                "Then try downloading again."
            )
            return
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self,
                "Connection Timeout",
                "Ollama server is not responding.\n\n"
                "Please check that Ollama is running properly."
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Cannot connect to Ollama server:\n{str(e)}\n\n"
                "Please make sure Ollama is running."
            )
            return

        # Get model name — custom input is passed directly to Ollama; bad names
        # are surfaced by the download worker's error signal instead of a pre-flight check.
        if self.custom_input_widget.isVisible() and self.custom_model_input.text().strip():
            model_name = self.custom_model_input.text().strip()
        elif self.selected_model:
            model_name = self.selected_model['model_id']
        else:
            QMessageBox.warning(self, "Error", "Please select a model or enter a custom model name!")
            return

        # Check if model already exists
        installed_models = [model["name"] for model in data.get("models", [])]

        # Check for exact match or base model match (e.g., llama3.2 matches llama3.2:latest)
        model_exists = False
        for installed in installed_models:
            # Check exact match or base match
            if installed == model_name or installed.startswith(model_name + ":") or model_name.startswith(installed.split(":")[0]):
                model_exists = True
                break

        if model_exists:
            QMessageBox.information(
                self,
                "Model Already Downloaded",
                f"The model '{model_name}' is already downloaded.\n\n"
                "You can find it in the model dropdown in the main window."
            )
            return

        # Reset cancellation flag
        self.download_canceled = False

        # Check internet connectivity before starting — Ollama pull requires
        # access to the Ollama registry even when the server is running locally.
        try:
            requests.get("https://ollama.com", timeout=5)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            QMessageBox.critical(
                self,
                "No Internet Connection",
                "Cannot download model: no internet connection detected.\n\n"
                "Please check your network and try again."
            )
            return

        # Disable UI
        self.download_btn.setEnabled(False)
        self.search_input.setEnabled(False)
        self.custom_model_input.setEnabled(False)
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Starting download of {model_name}...")
        self.progress_label.setStyleSheet("color: #007AFF; font-weight: bold;")

        # Change cancel button text
        self.cancel_btn.setText("Cancel Download")

        # Start download worker
        self.worker = ModelDownloadWorker(model_name)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)
        self.worker.start()

    def update_progress(self, message):
        """Update the progress label and bar"""
        self.progress_label.setText(message)

        # Try to extract percentage from message
        import re
        match = re.search(r'(\d+\.?\d*)%', message)
        if match:
            try:
                percentage = float(match.group(1))
                self.progress_bar.setValue(int(percentage))
            except:
                pass

    def download_finished(self):
        """Handle successful download"""
        # Don't show success if download was canceled
        if self.download_canceled:
            return

        self.progress_bar.setValue(100)
        self.progress_label.setText("✅ Download complete!")
        self.progress_label.setStyleSheet("color: #28a745; font-weight: bold;")
        QMessageBox.information(self, "Success", "Model downloaded successfully!")
        self.accept()

    def download_error(self, error):
        """Handle download error"""
        self.progress_label.setText(f"❌ Error: {error}")
        self.progress_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.custom_model_input.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        QMessageBox.critical(self, "Error", f"Failed to download model: {error}")

    def cancel_download(self):
        """Cancel the download"""
        if self.worker and self.worker.isRunning():
            # Download is in progress, stop it
            reply = QMessageBox.question(
                self,
                "Cancel Download",
                "Are you sure you want to cancel the download?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Set the canceled flag BEFORE stopping worker
                self.download_canceled = True

                self.worker.stop()
                self.worker.wait()

                # Update UI to show cancellation
                self.progress_label.setText("⚠️ Download canceled")
                self.progress_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                self.progress_bar.setVisible(False)
                self.download_btn.setEnabled(True)
                self.search_input.setEnabled(True)
                self.custom_model_input.setEnabled(True)
                self.cancel_btn.setText("Cancel")
        else:
            # No download in progress, just close the dialog
            self.reject()