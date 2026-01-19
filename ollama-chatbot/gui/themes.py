"""
Theme definitions for the Ollama Chatbot GUI
"""

LIGHT_THEME = """
    QMainWindow, QWidget { background-color: #f8f9fa; color: #212529; }
    QTextEdit { background-color: #ffffff; color: #212529; border: 1px solid #dee2e6; 
                border-radius: 12px; padding: 8px; font-size: 14px; }
    QPushButton { background-color: #007AFF; color: white; border: none; 
                  border-radius: 15px; padding: 10px 15px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
    QPushButton:disabled { background-color: #c0c0c0; }
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
    QPushButton:disabled { background-color: #4a4a4a; }
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