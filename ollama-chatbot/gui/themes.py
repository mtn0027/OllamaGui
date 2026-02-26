"""
Theme definitions and design tokens for the Ollama Chatbot GUI.

This module centralizes colors, typography, spacing, and radii and then
builds the light/dark Qt style sheets from those tokens.
"""

# -----------------------------------------------------------------------------
# Design tokens
# -----------------------------------------------------------------------------

# Typography
BASE_FONT_FAMILY = "'Segoe UI', 'Inter', 'Arial', sans-serif"
CODE_FONT_FAMILY = "'Consolas', 'Monaco', 'Courier New', monospace"

FONT_SIZE_CAPTION = 11
FONT_SIZE_BODY = 13
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_TITLE = 18

# Spacing scale (px)
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24

# Radii (px)
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 16
RADIUS_PILL = 999


LIGHT_TOKENS = {
    "bg_window": "#f8f9fa",
    "bg_surface": "#ffffff",
    "bg_surface_alt": "#f1f3f5",
    "bg_sidebar": "#ffffff",
    "bg_sidebar_border": "#dee2e6",
    "bg_input": "#ffffff",
    "bg_code": "#1e1e1e",
    "bg_scrollbar": "#f8f9fa",
    "bg_scrollbar_handle": "#c0c0c0",
    "bg_scrollbar_handle_hover": "#a0a0a0",
    "bg_scrollbar_handle_active": "#808080",
    "text_primary": "#212529",
    "text_muted": "#6c757d",
    "text_inverse": "#ffffff",
    "primary": "#007AFF",
    "primary_hover": "#0056b3",
    "primary_soft": "rgba(0, 122, 255, 0.08)",
    "primary_soft_border": "rgba(0, 122, 255, 0.2)",
    "success": "#28a745",
    "success_hover": "#218838",
    "danger": "#dc3545",
    "danger_hover": "#c82333",
    "border_subtle": "#dee2e6",
    "border_muted": "#ced4da",
    "border_strong": "#adb5bd",
    "shadow_soft": "0 4px 12px rgba(15, 23, 42, 0.08)",
}


DARK_TOKENS = {
    "bg_window": "#1e1e1e",
    "bg_surface": "#252525",
    "bg_surface_alt": "#2d2d2d",
    "bg_sidebar": "#252525",
    "bg_sidebar_border": "#404040",
    "bg_input": "#1e1e1e",
    "bg_code": "#1e1e1e",
    "bg_scrollbar": "#1e1e1e",
    "bg_scrollbar_handle": "#4a4a4a",
    "bg_scrollbar_handle_hover": "#5a5a5a",
    "bg_scrollbar_handle_active": "#6a6a6a",
    "text_primary": "#ffffff",
    "text_muted": "#a0a0a0",
    "text_inverse": "#000000",
    "primary": "#4C9DFF",
    "primary_hover": "#2F7AE5",
    "primary_soft": "rgba(76, 157, 255, 0.16)",
    "primary_soft_border": "rgba(76, 157, 255, 0.35)",
    "success": "#3FCF8E",
    "success_hover": "#31B77A",
    "danger": "#f15b6c",
    "danger_hover": "#d64759",
    "border_subtle": "#404040",
    "border_muted": "#3a3a3a",
    "border_strong": "#2c2c2c",
    "shadow_soft": "0 4px 18px rgba(0, 0, 0, 0.55)",
}


def _build_common_app_styles(tokens: dict) -> str:
    """Styles shared between light and dark themes."""
    return f"""
    QMainWindow, QWidget {{
        background-color: {tokens['bg_window']};
        color: {tokens['text_primary']};
        font-family: {BASE_FONT_FAMILY};
        font-size: {FONT_SIZE_BODY}px;
    }}

    /* Text inputs / editors */
    QTextEdit, QLineEdit {{
        background-color: {tokens['bg_input']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['border_subtle']};
        border-radius: {RADIUS_LG}px;
        padding: {SPACE_SM}px {SPACE_MD}px;
        font-size: {FONT_SIZE_BODY}px;
    }}

    /* Generic push buttons (used as base for variants) */
    QPushButton {{
        background-color: {tokens['primary']};
        color: {tokens['text_inverse']};
        border: none;
        border-radius: {RADIUS_LG}px;
        padding: {SPACE_SM + 2}px {SPACE_LG}px;
        font-weight: 600;
        font-size: {FONT_SIZE_BODY}px;
    }}
    QPushButton:hover {{
        background-color: {tokens['primary_hover']};
    }}
    QPushButton:disabled {{
        background-color: {tokens['border_muted']};
        color: {tokens['text_muted']};
    }}

    /* Icon-only circular buttons used in the top bar */
    QPushButton#circularBtn {{
        background-color: transparent;
        border-radius: 22px;
        border: 1px solid {tokens['border_subtle']};
    }}
    QPushButton#circularBtn:hover {{
        background-color: {tokens['primary_soft']};
        border-color: {tokens['primary']};
    }}

    /* Button variants — controlled via objectName */
    QPushButton#primaryButton {{
        background-color: {tokens['primary']};
        color: {tokens['text_inverse']};
        border-radius: {RADIUS_LG}px;
        padding: {SPACE_SM + 2}px {SPACE_LG}px;
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {tokens['primary_hover']};
    }}

    QPushButton#secondaryButton {{
        background-color: {tokens['bg_surface_alt']};
        color: {tokens['text_primary']};
        border-radius: {RADIUS_LG}px;
        border: 1px solid {tokens['border_subtle']};
        padding: {SPACE_SM + 2}px {SPACE_LG}px;
        font-weight: 500;
    }}
    QPushButton#secondaryButton:hover {{
        background-color: {tokens['primary_soft']};
        border-color: {tokens['primary']};
    }}

    QPushButton#dangerButton {{
        background-color: {tokens['danger']};
        color: {tokens['text_inverse']};
        border-radius: {RADIUS_LG}px;
        padding: {SPACE_SM + 2}px {SPACE_LG}px;
        font-weight: 600;
    }}
    QPushButton#dangerButton:hover {{
        background-color: {tokens['danger_hover']};
    }}

    QPushButton#ghostIconButton {{
        background-color: transparent;
        border-radius: 18px;
        border: 1px solid {tokens['border_subtle']};
        padding: {SPACE_XS}px {SPACE_SM}px;
    }}
    QPushButton#ghostIconButton:hover {{
        background-color: {tokens['primary_soft']};
        border-color: {tokens['primary']};
    }}

    /* Combo box & list */
    QComboBox, QListWidget {{
        background-color: {tokens['bg_surface']};
        color: {tokens['text_primary']};
        border: 1px solid {tokens['border_subtle']};
        border-radius: {RADIUS_MD}px;
        padding: {SPACE_SM}px;
    }}
    QListWidget::item {{
        padding: {SPACE_SM + 2}px;
        border-radius: {RADIUS_MD}px;
        margin: 2px;
    }}
    QListWidget::item:selected {{
        background-color: {tokens['primary']};
        color: {tokens['text_inverse']};
    }}

    /* Sidebar */
    AnimatedSidebar {{
        background-color: {tokens['bg_sidebar']};
        border-right: 1px solid {tokens['bg_sidebar_border']};
    }}

    QLabel#sidebarTitle {{
        font-size: {FONT_SIZE_TITLE}px;
        font-weight: 600;
    }}

    QLabel#sidebarHint, QLabel#mutedLabel {{
        color: {tokens['text_muted']};
        font-size: {FONT_SIZE_CAPTION}px;
    }}

    /* Scroll-to-bottom floating button */
    QPushButton#scrollBottomButton {{
        background-color: {tokens['primary']};
        color: {tokens['text_inverse']};
        border: 2px solid {tokens['bg_surface']};
        border-radius: 25px;
        font-size: 22px;
        font-weight: 700;
        box-shadow: {tokens['shadow_soft']};
    }}
    QPushButton#scrollBottomButton:hover {{
        background-color: {tokens['primary_hover']};
    }}

    /* Custom Scrollbar Styling */
    QScrollBar:vertical {{
        background: {tokens['bg_scrollbar']};
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {tokens['bg_scrollbar_handle']};
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {tokens['bg_scrollbar_handle_hover']};
    }}
    QScrollBar::handle:vertical:pressed {{
        background: {tokens['bg_scrollbar_handle_active']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: {tokens['bg_scrollbar']};
        height: 12px;
        border-radius: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {tokens['bg_scrollbar_handle']};
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {tokens['bg_scrollbar_handle_hover']};
    }}
    QScrollBar::handle:horizontal:pressed {{
        background: {tokens['bg_scrollbar_handle_active']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    """


def _build_light_theme() -> str:
    """Return the full light theme style sheet."""
    tokens = LIGHT_TOKENS
    base = _build_common_app_styles(tokens)
    return base


def _build_dark_theme() -> str:
    """Return the full dark theme style sheet."""
    tokens = DARK_TOKENS
    base = _build_common_app_styles(tokens)

    # Override circular top-bar buttons to be more visible against the dark background.
    # The shared style uses `transparent` which makes them hard to spot; a subtle
    # tinted surface and a lighter border fix this without breaking the design language.
    dark_overrides = """
    QPushButton#circularBtn {
        background-color: rgba(255, 255, 255, 0.07);
        border: 1px solid #5a5a5a;
        border-radius: 22px;
    }
    QPushButton#circularBtn:hover {
        background-color: rgba(76, 157, 255, 0.20);
        border-color: #4C9DFF;
    }
    """

    return base + dark_overrides


# Final style sheet strings used by the app
LIGHT_THEME = _build_light_theme()
DARK_THEME = _build_dark_theme()