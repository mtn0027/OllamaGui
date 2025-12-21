"""
GUI package for Ollama Chatbot
"""

from .main_window import ChatbotGUI
from .widgets import MessageBubble, AnimatedSidebar
from .dialogs import SettingsDialog, ModelDownloadDialog

__all__ = ['ChatbotGUI', 'MessageBubble', 'AnimatedSidebar', 'SettingsDialog', 'ModelDownloadDialog']