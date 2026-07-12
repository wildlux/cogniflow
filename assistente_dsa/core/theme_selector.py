"""
Modulo per la selezione e gestione dei temi
"""

from typing import cast

try:
    from .config_module import get_setting, set_setting
except ImportError:
    from config_module import get_setting, set_setting

def select_theme():
    """Seleziona il primo tema disponibile"""
    print("\n🎨 Selezione tema...")
    themes = get_setting("themes.available", [])
    if themes:
        selected_theme = cast(str, themes[0]["name"])
        set_setting("themes.selected", selected_theme)
        print(f"✅ Tema selezionato: {selected_theme}")
        return selected_theme
    return "Professionale"

def get_current_theme():
    """Restituisce il tema attualmente selezionato"""
    return get_setting("themes.selected", "Professionale")

def list_available_themes():
    """Restituisce la lista dei temi disponibili"""
    return get_setting("themes.available", [])