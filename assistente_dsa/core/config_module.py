import os, json
from typing import cast, Any

def load_settings():
    """Load settings from file or return defaults"""
    settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "SETUP_TOOLS_&_Data", "settings.json")

    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Default settings
    return {
        "application": {"theme": "Professionale"},
        "ui": {"window_width": 1200, "window_height": 800},
        "themes": {
            "selected": "Professionale",
            "available": [
                {"name": "Professionale", "icon": "💼", "description": "Per professionisti"},
                {"name": "Studente", "icon": "🎒", "description": "Per studenti"},
                {"name": "Chimico", "icon": "🥽", "description": "Per chimici"},
                {"name": "Donna", "icon": "👝", "description": "Per donne"},
                {"name": "Artigiano", "icon": "🧰", "description": "Per artigiani"},
                {"name": "Specchio", "icon": "🪞", "description": "Tema specchio"},
                {"name": "Magico", "icon": "🪄", "description": "Tema magico"},
                {"name": "Pensieri", "icon": "💭", "description": "Tema pensieri"},
                {"name": "Nuvola", "icon": "🗯", "description": "Tema nuvola"},
                {"name": "Audio", "icon": "🔊", "description": "Tema audio"},
                {"name": "Chat", "icon": "💬", "description": "Tema chat"}
            ]
        },
        "startup": {"bypass_login": True}
    }

def get_setting(key: str, default=None):
    """Get a setting value"""
    settings = load_settings()
    keys = key.split(".")
    value = settings
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def set_setting(key: str, value):
    """Set a setting value"""
    settings = load_settings()
    keys = key.split(".")
    current = settings
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value

    # Save to file
    settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Save", "SETUP_TOOLS_&_Data", "settings.json")
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)