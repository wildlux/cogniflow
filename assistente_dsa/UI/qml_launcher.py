#!/usr/bin/env python3
"""
Launcher per l'interfaccia QML con integrazione Ollama e MediaPipe
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
    """Avvia l'applicazione QML con i bridge"""
    app = QApplication(sys.argv)

    # Crea il motore QML
    engine = QQmlApplicationEngine()

    # Registra il bridge Ollama nel contesto QML
    bridge = register_bridge(engine)

    # Registra il bridge MediaPipe nel contesto QML
    if register_mediapipe_bridge:
        mediapipe_bridge = register_mediapipe_bridge(engine)
        print("✅ MediaPipe bridge registrato")
    else:
        print("⚠️ MediaPipe bridge non disponibile")

    # Carica il file QML
    qml_file = os.path.join(os.path.dirname(__file__), "main_interface.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        print("❌ Errore nel caricamento del file QML")
        return -1

    print("✅ Interfaccia QML avviata con integrazione Ollama e MediaPipe")

    # Avvia l'applicazione
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
