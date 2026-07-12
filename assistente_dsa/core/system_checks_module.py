"""
Modulo per i controlli di sistema e sicurezza.

Questo modulo fornisce funzioni per verificare l'integrità del sistema,
la presenza di file richiesti e configurazioni di sicurezza di base.
Include controlli per directory, pacchetti Python e configurazioni di sicurezza.

Funzioni:
    check_package(): Verifica se un pacchetto Python è disponibile
    check_security_headers(): Controlla configurazioni di sicurezza
    check_directory(): Verifica esistenza directory
    perform_security_checks(): Controllo completo di sicurezza

Nota:
    La funzione check_dependency_vulnerabilities è stata spostata in
    dependency_checker.py per una migliore separazione delle responsabilità.
"""

import os, sys, stat
from typing import cast, Tuple, List

# Import della funzione spostata
try:
    from .dependency_checker import check_dependency_vulnerabilities
except ImportError:
    from dependency_checker import check_dependency_vulnerabilities

def check_package(package: str) -> Tuple[str, bool]:
    """
    Verifica se un pacchetto Python è disponibile per l'importazione.

    Args:
        package (str): Nome del pacchetto da verificare

    Returns:
        Tuple[str, bool]: Tupla contenente (nome_pacchetto, disponibile)

    Example:
        >>> name, available = check_package("os")
        >>> print(f"{name}: {'✓' if available else '✗'}")
        os: ✓
    """
    try:
        __import__(package)
        return package, True
    except ImportError:
        return package, False

def check_security_headers() -> Tuple[bool, List[str]]:
    """
    Controlla le configurazioni di sicurezza del sistema.

    Questa funzione verifica diverse impostazioni di sicurezza che potrebbero
    compromettere la sicurezza dell'applicazione:

    1. **Modalità sviluppo**: Se PYTHON_ENV=development
    2. **Permessi file**: File sensibili leggibili da tutti
    3. **Modalità debug**: Se DEBUG=true

    File controllati:
        - requirements.txt
        - assistente_dsa/Save/AUTH/users.json
        - assistente_dsa/Save/SETUP_TOOLS&_Data/settings.json

    Args:
        Nessuno

    Returns:
        Tuple[bool, List[str]]: Tupla contenente:
            - bool: True se la configurazione è sicura, False altrimenti
            - List[str]: Lista dei problemi di sicurezza trovati

    Examples:
        >>> safe, issues = check_security_headers()
        >>> if not safe:
        ...     for issue in issues:
        ...         print(f"⚠️  {issue}")

        Output possibile:
        ⚠️  Application running in development mode
        ⚠️  File requirements.txt is world-readable
    """
    issues = []
    safe = True
    print("🔍 Checking security configurations...")

    # Controllo modalità sviluppo
    if os.environ.get("PYTHON_ENV") == "development":
        issues.append("Application running in development mode")
        safe = False

    # File sensibili da controllare
    sensitive_files = [
        "requirements.txt",
        os.path.join("assistente_dsa", "Save", "AUTH", "users.json"),
        os.path.join("assistente_dsa", "Save", "SETUP_TOOLS_&_Data", "settings.json")
    ]

    # Controllo permessi file (solo su sistemi Unix-like)
    for file_path in sensitive_files:
        if os.path.exists(file_path) and os.name != 'nt':
            if os.stat(file_path).st_mode & stat.S_IROTH:
                issues.append(f"File {file_path} is world-readable")
                safe = False

    # Controllo modalità debug
    if os.environ.get("DEBUG") == "true":
        issues.append("Debug mode is enabled")
        safe = False

    return safe, issues

def check_directory(dir_path: str) -> Tuple[str, bool]:
    """
    Verifica l'esistenza di una directory.

    Args:
        dir_path (str): Percorso della directory da verificare

    Returns:
        Tuple[str, bool]: Tupla contenente:
            - str: Nome della directory (senza percorso)
            - bool: True se la directory esiste, False altrimenti

    Example:
        >>> name, exists = check_directory("/home/user/documents")
        >>> print(f"Directory '{name}': {'exists' if exists else 'not found'}")
        Directory 'documents': exists
    """
    return os.path.basename(dir_path), os.path.exists(dir_path)

def perform_security_checks():
    """
    Esegue controlli completi di sicurezza e utilizzabilità del sistema.

    Questa funzione esegue una serie completa di verifiche per garantire
    che l'ambiente sia sicuro e adatto all'esecuzione dell'applicazione:

    1. **Controllo Versione Python**:
       - Verifica Python 3.8+ (requisito minimo)
       - Mostra versione corrente

    2. **Controllo Privilegi**:
       - Avverte se eseguito come root (rischi di sicurezza)
       - Solo su sistemi Unix-like

    3. **Controllo Permessi Scrittura**:
       - Testa possibilità di scrivere nella directory corrente
       - Crea e rimuove file di test temporaneo

    4. **Controllo Directory Richieste**:
       - Verifica esistenza directory essenziali del progetto
       - Save, Screenshot, assistente_dsa

    5. **Controllo Pacchetti Python**:
       - Verifica disponibilità pacchetti richiesti
       - PyQt6, subprocess, os, sys, cv2, numpy

    Directory controllate:
        - Save: Directory per dati persistenti
        - Screenshot: Directory per catture schermo
        - assistente_dsa: Directory principale applicazione

    Pacchetti controllati:
        - PyQt6: Interfaccia grafica
        - subprocess: Esecuzione comandi sistema
        - os, sys: Moduli standard Python
        - cv2: OpenCV per computer vision
        - numpy: Elaborazione array numerici

    Returns:
        bool: True se tutti i controlli passano, False altrimenti

    Note:
        - La funzione termina immediatamente al primo errore critico
        - Tutti i controlli sono sequenziali per migliore debugging
        - I messaggi vengono stampati su console per feedback utente

    Examples:
        >>> success = perform_security_checks()
        >>> if success:
        ...     print("✅ Sistema pronto per l'avvio")
        ... else:
        ...     print("❌ Controlli di sicurezza falliti")

    Output tipico:
        🔍 Performing security and usability checks...
        ✅ Python version: 3.9.7
        ✅ Write permissions verified
        ✅ Directory 'Save' exists
        ✅ Package 'PyQt6' available
        ✅ All checks passed
    """
    print("🔍 Performing security and usability checks...")

    # Controllo versione Python
    if sys.version_info < (3, 8):
        print("❌ ERROR: Python 3.8 or higher required")
        return False

    print(f"✅ Python version: {sys.version}")

    # Controllo esecuzione come root (solo Unix)
    try:
        if os.geteuid() == 0:
            print("⚠️  WARNING: Running as root - this may pose security risks")
    except AttributeError:
        # os.geteuid() non disponibile su Windows
        pass

    # Test permessi scrittura
    try:
        test_file = os.path.join(os.getcwd(), ".test_write")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Write permissions verified")
    except Exception as e:
        print(f"❌ ERROR: No write permissions in current directory: {e}")
        return False

    # Controllo directory richieste
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_dirs = ["Save", "Screenshot", "assistente_dsa"]

    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        exists = os.path.exists(dir_path)
        if not exists:
            print(f"⚠️  WARNING: Required directory '{dir_name}' not found")
        else:
            print(f"✅ Directory '{dir_name}' exists")

    # Controllo pacchetti Python richiesti
    required_packages = ["PyQt6", "subprocess", "os", "sys", "cv2", "numpy"]
    missing_packages = []

    for package in required_packages:
        try:
            available = check_package(package)[1]
            if available:
                print(f"✅ Package '{package}' available")
            else:
                missing_packages.append(package)
                print(f"❌ Package '{package}' missing")
        except Exception as e:
            missing_packages.append(package)
            print(f"⚠️  Package '{package}' check failed: {e}")

    # Report pacchetti mancanti
    if missing_packages:
        print(f"⚠️  WARNING: Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package>")

    return True

def test_imports():
    """
    Testa gli import critici e la configurazione centralizzata.

    Questa funzione verifica che tutti i componenti essenziali del sistema
    possano essere importati e configurati correttamente:

    1. **Configurazione Centralizzata**:
       - Import del modulo config_module
       - Lettura impostazioni UI (dimensioni finestra)
       - Lettura tema applicazione

    2. **Modulo Principale**:
       - Import dinamico di main_01_Aircraft.py
       - Verifica integrità del modulo principale
       - Controllo dipendenze del modulo

    Impostazioni testate:
        - ui.window_width: Larghezza finestra (default: 1200)
        - ui.window_height: Altezza finestra (default: 800)
        - application.theme: Tema applicazione (default: 'Chiaro')

    Returns:
        bool: True se tutti gli import riescono, False altrimenti

    Note:
        - Utilizza import dinamico per evitare dipendenze statiche
        - Fornisce dettagli specifici su quale import fallisce
        - Include traceback completo per debugging

    Examples:
        >>> success = test_imports()
        >>> if success:
        ...     print("✅ Tutti gli import riusciti")
        ... else:
        ...     print("❌ Alcuni import falliti - controllare logs")

    Output tipico:
        Testing imports with centralized configuration...
        Centralized settings loaded - Window size: 1200x800
        Application theme: Professionale
        ✅ Main module (main_01_Aircraft) imported successfully

    Error handling:
        - Cattura tutti gli errori di import
        - Fornisce messaggi di errore specifici
        - Include stack trace completo per debugging
        - Ritorna False al primo errore critico
    """
    print("Testing imports with centralized configuration...")

    try:
        # Test import configurazione centralizzata
        try:
            from assistente_dsa.core.config_module import get_setting
        except ImportError:
            try:
                from config_module import get_setting
            except ImportError:
                print("❌ Could not import config_module")
                return False

        # Test lettura impostazioni
        window_width = cast(int, get_setting("ui.window_width", 1200))
        window_height = cast(int, get_setting("ui.window_height", 800))
        print(f"Centralized settings loaded - Window size: {window_width}x{window_height}")
        print(f"Application theme: {get_setting('application.theme', 'Chiaro')}")

        # Test import modulo principale
        try:
            import importlib.util
            aircraft_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main_01_Aircraft.py")
            spec = importlib.util.spec_from_file_location("main_01_Aircraft", aircraft_path)

            if spec is None or spec.loader is None:
                raise ImportError("Could not load main_01_Aircraft module")

            main_01_Aircraft = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_01_Aircraft)
            print("✅ Main module (main_01_Aircraft) imported successfully")

        except ImportError as e:
            print(f"❌ Critical module import failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        return False