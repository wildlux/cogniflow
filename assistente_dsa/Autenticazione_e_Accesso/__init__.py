# Autenticazione e Accesso - Modulo per la gestione dell'autenticazione
"""
Modulo Autenticazione_e_Accesso

Questo modulo contiene tutti i componenti relativi all'autenticazione e gestione degli accessi
dell'applicazione DSA Assistant.

Componenti principali:
- Gestione utenti e autenticazione
- Dialog di login e registrazione
- Recupero password
- Sicurezza e crittografia
- Flussi di autenticazione
"""

__version__ = "1.0.0"
__author__ = "DSA Assistant Team"

# Import principali per accesso facilitato
from .auth_manager import *
from .login_dialog import *
from .auth_flow import *
from .auth_module import *
from .app_launcher import *
from .gui_components import *
from .security_utils import *

__all__ = [
    'auth_manager',
    'login_dialog',
    'password_reset_dialog',
    'auth_flow',
    'auth_module',
    'simple_auth',
    'simple_auth_manager',
    'user_auth_manager',
    'app_launcher',
    'gui_components',
    'security_utils',
    'test_auth_setup'
]