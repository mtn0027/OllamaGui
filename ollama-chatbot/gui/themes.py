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


# -----------------------------------------------------------------------------
# Accent color helpers
# -----------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert a hex color string to an (r, g, b) tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


def _darken(hex_color: str, factor: float = 0.20) -> str:
    """Return a darkened version of *hex_color* by reducing each channel by *factor*."""
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgba(hex_color: str, opacity: float) -> str:
    """Return an rgba() string for *hex_color* at the given *opacity* (0–1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {opacity})"


def _build_light_tokens(accent: str = "#007AFF") -> dict:
    """Build and return the light-theme token dict for the given accent color."""
    return {
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
        "primary": accent,
        "primary_hover": _darken(accent, 0.20),
        "primary_soft": _rgba(accent, 0.08),
        "primary_soft_border": _rgba(accent, 0.20),
        "success": "#28a745",
        "success_hover": "#218838",
        "danger": "#dc3545",
        "danger_hover": "#c82333",
        "border_subtle": "#dee2e6",
        "border_muted": "#ced4da",
        "border_strong": "#adb5bd",
        "shadow_soft": "0 4px 12px rgba(15, 23, 42, 0.08)",
    }


def _build_dark_tokens(accent: str = "#007AFF") -> dict:
    """Build and return the dark-theme token dict for the given accent color."""
    return {
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
        "primary": accent,
        "primary_hover": _darken(accent, 0.20),
        "primary_soft": _rgba(accent, 0.16),
        "primary_soft_border": _rgba(accent, 0.35),
        "success": "#3FCF8E",
        "success_hover": "#31B77A",
        "danger": "#f15b6c",
        "danger_hover": "#d64759",
        "border_subtle": "#404040",
        "border_muted": "#3a3a3a",
        "border_strong": "#2c2c2c",
        "shadow_soft": "0 4px 18px rgba(0, 0, 0, 0.55)",
    }


# Module-level token dicts built with the default accent (kept for backwards compatibility)
LIGHT_TOKENS = _build_light_tokens()
DARK_TOKENS = _build_dark_tokens()


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


# -----------------------------------------------------------------------------
# Public builder functions
# -----------------------------------------------------------------------------

def build_light_theme(accent: str = "#007AFF") -> str:
    """Return a complete light theme style sheet built around *accent*."""
    tokens = _build_light_tokens(accent)
    return _build_common_app_styles(tokens)


def build_dark_theme(accent: str = "#007AFF") -> str:
    """Return a complete dark theme style sheet built around *accent*.

    Includes dark-specific overrides for the circular top-bar buttons so they
    remain visible against the dark background.
    """
    tokens = _build_dark_tokens(accent)
    base = _build_common_app_styles(tokens)

    # Override circular top-bar buttons to be more visible against the dark background.
    # The shared style uses `transparent` which makes them hard to spot; a subtle
    # tinted surface and a lighter border fix this without breaking the design language.
    dark_overrides = f"""
    QPushButton#circularBtn {{
        background-color: rgba(255, 255, 255, 0.07);
        border: 1px solid #5a5a5a;
        border-radius: 22px;
    }}
    QPushButton#circularBtn:hover {{
        background-color: {_rgba(accent, 0.20)};
        border-color: {accent};
    }}
    """

    return base + dark_overrides


# -----------------------------------------------------------------------------
# Module-level constants (default accent) — kept for backwards compatibility
# -----------------------------------------------------------------------------

LIGHT_THEME = build_light_theme()
DARK_THEME = build_dark_theme()