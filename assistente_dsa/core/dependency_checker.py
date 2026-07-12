"""
Modulo per il controllo delle vulnerabilità delle dipendenze.

Questo modulo fornisce funzionalità per analizzare le dipendenze Python
installate e identificare vulnerabilità di sicurezza note. Supporta sia
l'uso di strumenti esterni come pip-audit che controlli manuali.

Funzioni:
    check_dependency_vulnerabilities(): Controllo principale delle vulnerabilità

Strumenti supportati:
    - pip-audit: Strumento automatico per audit delle dipendenze
    - Controllo manuale: Basato su database di vulnerabilità note

Database vulnerabilità:
    - PyQt6: Versioni 6.0.0, 6.0.1, 6.0.2
    - requests: Versioni 2.20.0, 2.20.1
    - urllib3: Versioni 1.24.0, 1.24.1, 1.24.2

Esempio:
    >>> from core.dependency_checker import check_dependency_vulnerabilities
    >>> safe, vulnerabilities = check_dependency_vulnerabilities()
    >>> if not safe:
    ...     print(f"Trovate {len(vulnerabilities)} vulnerabilità")
"""

import subprocess
import sys
from typing import Tuple, List
from importlib.metadata import distributions

def check_dependency_vulnerabilities() -> Tuple[bool, List[str]]:
    """
    Controlla le vulnerabilità delle dipendenze Python installate.

    Questa funzione esegue un controllo completo delle dipendenze per
    identificare vulnerabilità di sicurezza note. Utilizza due approcci:

    1. **Controllo automatico con pip-audit**:
       - Utilizza lo strumento pip-audit se disponibile
       - Fornisce audit completo e aggiornato
       - Timeout di 30 secondi per evitare blocchi

    2. **Controllo manuale**:
       - Database locale di vulnerabilità note
       - Controllo versioni specifiche note per essere vulnerabili
       - Fallback quando pip-audit non è disponibile

    Database vulnerabilità incluse:
        - PyQt6: 6.0.0, 6.0.1, 6.0.2 (vulnerabilità note)
        - requests: 2.20.0, 2.20.1 (problemi di sicurezza)
        - urllib3: 1.24.0, 1.24.1, 1.24.2 (vulnerabilità SSL)

    Returns:
        Tuple[bool, List[str]]: Una tupla contenente:
            - bool: True se non sono state trovate vulnerabilità, False altrimenti
            - List[str]: Lista delle vulnerabilità trovate, vuota se sicura

    Formato vulnerabilità:
        Ogni stringa nella lista segue il formato:
        "nome_pacchetto versione: descrizione_vulnerabilità"

    Examples:
        >>> safe, vulns = check_dependency_vulnerabilities()
        >>> if not safe:
        ...     for vuln in vulns:
        ...         print(f"⚠️  {vuln}")

        Output possibile:
        ⚠️  PyQt6 6.0.1: Known vulnerable version
        ⚠️  requests 2.20.0: SSL verification bypass

    Note:
        - La funzione richiede pip-audit per controlli automatici completi
        - Il database manuale è limitato e dovrebbe essere aggiornato regolarmente
        - In caso di errore, viene restituito (False, [messaggio_errore])

    Raises:
        Nessuno: Tutti gli errori sono gestiti internamente

    Performance:
        - Controllo pip-audit: ~5-30 secondi
        - Controllo manuale: ~0.1 secondi
        - Timeout automatico per evitare blocchi
    """
    vulnerabilities = []
    safe = True
    print("🔍 Checking dependency vulnerabilities...")

    # Database delle vulnerabilità note
    vulnerable_packages = {
        "PyQt6": ["6.0.0", "6.0.1", "6.0.2"],  # Esempi di versioni vulnerabili
        "requests": ["2.20.0", "2.20.1"],      # Problemi SSL
        "urllib3": ["1.24.0", "1.24.1", "1.24.2"]  # Vulnerabilità SSL
    }

    # Tentativo di controllo automatico con pip-audit
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            import json
            audit_data = json.loads(result.stdout)

            for vuln in audit_data:
                vuln_description = f"{vuln['name']} {vuln['version']}: {vuln['description']}"
                vulnerabilities.append(vuln_description)
                safe = False

            print("✅ Dependency audit completed using pip-audit")
            return safe, vulnerabilities

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # pip-audit non disponibile o timeout, procedi con controllo manuale
        pass
    except Exception as e:
        vulnerabilities.append(f"pip-audit error: {e}")
        return False, vulnerabilities

    # Controllo manuale basato su database locale
    try:
        installed_packages = {dist.name: dist.version for dist in distributions()}

        for package, vulnerable_versions in vulnerable_packages.items():
            if package in installed_packages:
                current_version = installed_packages[package]
                if current_version in vulnerable_versions:
                    vuln_description = f"{package} {current_version}: Known vulnerable version"
                    vulnerabilities.append(vuln_description)
                    safe = False

        print("✅ Manual dependency vulnerability check completed")
        return safe, vulnerabilities

    except Exception as e:
        error_msg = f"Could not check vulnerabilities: {e}"
        vulnerabilities.append(error_msg)
        return False, vulnerabilities