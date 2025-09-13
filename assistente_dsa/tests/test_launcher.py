#!/usr/bin/env python3
"""
Simple test launcher for MediaPipe integration
"""

import os
import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

# Aggiungi i percorsi per importare i moduli
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import del bridge Ollama
from Artificial_Intelligence.Ollama.ollama_bridge import register_bridge

# Import del bridge MediaPipe
try:
    from services.mediapipe_bridge import register_mediapipe_bridge
except ImportError:
    register_mediapipe_bridge = None
    print("MediaPipe bridge non disponibile")


def main():
    """Avvia l'applicazione di test"""
    app = QApplication(sys.argv)

    # Crea il motore QML
    engine = QQmlApplicationEngine()

    # Registra il bridge Ollama nel contesto QML
    bridge = register_bridge(engine)

    # Registra il bridge MediaPipe nel contesto QML
    # No MediaPipe bridge to register
        print("✅ MediaPipe bridge registrato")
    else:
        print("⚠️ MediaPipe bridge non disponibile")

    # Carica il file QML di test
    qml_file = os.path.join(os.path.dirname(__file__), "test_interface.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        print("❌ Errore nel caricamento del file QML")
        return -1

    print("✅ Interfaccia di test avviata")

    # Avvia l'applicazione
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
