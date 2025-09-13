"""
Modulo per la gestione del flusso di autenticazione
"""

from typing import cast, Dict, Any

try:
    from ..core.config_module import get_setting
    from .auth_manager import auth_manager, AUTH_AVAILABLE
    from ..core.gui_module import open_launcher_gui
except ImportError:
    from core.config_module import get_setting
    from Autenticazione_e_Accesso.auth_manager import auth_manager, AUTH_AVAILABLE
    from core.gui_module import open_launcher_gui

def handle_authentication() -> Dict[str, Any]:
    """
    Gestisce il flusso di autenticazione completo
    Restituisce le informazioni dell'utente autenticato
    """
    bypass_login = cast(bool, get_setting("startup.bypass_login", True))
    print(f"🔐 Bypass login: {bypass_login}")

    if bypass_login:
        print("🔓 Modalità avvio diretto")
        return {
            "username": "admin",
            "full_name": "Administrator",
            "group": "Administrator"
        }
    else:
        print("🔐 Autenticazione richiesta")
        open_launcher_gui()
        return None  # La GUI gestisce il flusso

def check_permissions(user: Dict[str, Any]) -> Dict[str, bool]:
    """
    Verifica i permessi dell'utente
    """
    if AUTH_AVAILABLE and auth_manager:
        permissions = auth_manager.get_user_permissions(user["username"])
        if not permissions.get("system_access", False):
            print("❌ Accesso negato")
            return None
        return permissions
    else:
        return {"system_access": True, "ai_access": True}