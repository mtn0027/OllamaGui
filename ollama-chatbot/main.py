"""
Ollama Chatbot GUI - Main Entry Point
Run this file to start the application
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from gui.main_window import ChatbotGUI


def main():
    """Initialize and run the application"""
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont('Inter', 10))
        app.setStyleSheet("""
            * {
                font-family: 'Inter', 'Segoe UI', 'Arial', 'Helvetica', sans-serif;
            }
        """)

        window = ChatbotGUI()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()