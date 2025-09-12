#!/usr/bin/env python3
"""
Punto di ingresso principale per CogniFlow DSA Assistant.

Questo file gestisce l'avvio sicuro dell'applicazione con:
- Controlli di sicurezza
- Test delle importazioni critiche
- Avvio dell'interfaccia principale
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Configurazione logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Aggiungi la directory corrente al PYTHONPATH
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def test_critical_imports():
    """Testa le importazioni critiche prima dell'avvio."""
    logger.info("🔍 Testando importazioni critiche...")

    critical_imports = [
        ("PyQt6.QtWidgets", "Interfaccia grafica"),
        ("PyQt6.QtCore", "Core Qt"),
        ("main_01_Aircraft", "Interfaccia principale"),
        ("main_03_configurazione_e_opzioni", "Sistema configurazione"),
    ]

    failed_imports = []

    for module_name, description in critical_imports:
        try:
            __import__(module_name)
            logger.info(f"✅ {description}: OK")
        except ImportError as e:
            logger.error(f"❌ {description}: FALLITO - {e}")
            failed_imports.append((module_name, description, str(e)))
        except Exception as e:
            logger.warning(f"⚠️  {description}: ERRORE - {e}")

    if failed_imports:
        logger.error("❌ Importazioni critiche fallite:")
        for module, desc, error in failed_imports:
            logger.error(f"   - {desc} ({module}): {error}")
        return False

    logger.info("✅ Tutte le importazioni critiche riuscite")
    return True


def start_application():
    """Avvia l'applicazione principale."""
    try:
        logger.info("🚀 Avvio CogniFlow DSA Assistant...")

        # Import e avvio dell'interfaccia principale
        from main_01_Aircraft import main

        logger.info("✅ Interfaccia principale importata con successo")
        main()

    except ImportError as e:
        logger.error(f"❌ Errore importazione interfaccia: {e}")
        logger.error("💡 Assicurati che tutti i moduli siano installati")
        logger.error("💡 Prova: python -m pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ Errore avvio applicazione: {e}")
        logger.error(f"💡 Dettagli errore:\n{traceback.format_exc()}")
        return False

    return True


def main():
    """Funzione principale."""
    print("=" * 60)
    print("🤖 COGNIFLOW - DSA ASSISTANT")
    print("=" * 60)

    # Test importazioni critiche
    if not test_critical_imports():
        logger.error("❌ Impossibile avviare: importazioni critiche fallite")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎯 AVVIO APPLICAZIONE")
    print("=" * 60)

    # Avvia l'applicazione
    if start_application():
        logger.info("✅ Applicazione avviata con successo")
    else:
        logger.error("❌ Errore durante l'avvio dell'applicazione")
        sys.exit(1)


if __name__ == "__main__":
    main()
