# styles/__init__.py - Pacchetto per gli stili dell'applicazione

from .main_styles import get_main_stylesheet
from .widget_styles import DRAGGABLE_WIDGET_STYLE, LOG_WIDGET_STYLE, TEXT_INPUT_STYLE, AI_RESULTS_STYLE
from .panel_styles import get_scrollable_panel_style

__all__ = [
    'get_main_stylesheet',
    'DRAGGABLE_WIDGET_STYLE',
    'LOG_WIDGET_STYLE',
    'TEXT_INPUT_STYLE',
    'AI_RESULTS_STYLE',
    'get_scrollable_panel_style'
]