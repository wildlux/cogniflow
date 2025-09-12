#!/usr/bin/env python3
"""
Helper semplificato per la gestione delle dipendenze - DSA Assistant
Versione semplificata che funziona correttamente
"""

import logging
import sys
import os

# Configurazione logging
logger = logging.getLogger("DependencyHelper")

print("🔍 Controllo dipendenze DSA Assistant")
print("=" * 50)

# Test dipendenze critiche
dependencies_status = {}

# PyQt6
try:
    from PyQt6.QtWidgets import QApplication

    dependencies_status["PyQt6"] = "✅ Disponibile"
    print("PyQt6: ✅ Disponibile")
except ImportError:
    dependencies_status["PyQt6"] = "❌ Non disponibile"
    print("PyQt6: ❌ Non disponibile")

# OpenCV
try:
    import cv2

    dependencies_status["OpenCV"] = "✅ Disponibile"
    print("OpenCV: ✅ Disponibile")
except ImportError:
    dependencies_status["OpenCV"] = "❌ Non disponibile"
    print("OpenCV: ❌ Non disponibile")

# Numpy
try:
    import numpy as np

    dependencies_status["NumPy"] = "✅ Disponibile"
    print("NumPy: ✅ Disponibile")
except ImportError:
    dependencies_status["NumPy"] = "❌ Non disponibile"
    print("NumPy: ❌ Non disponibile")

# Pillow
try:
    from PIL import Image

    dependencies_status["Pillow"] = "✅ Disponibile"
    print("Pillow: ✅ Disponibile")
except ImportError:
    dependencies_status["Pillow"] = "❌ Non disponibile"
    print("Pillow: ❌ Non disponibile")

# Requests
try:
    import requests

    dependencies_status["Requests"] = "✅ Disponibile"
    print("Requests: ✅ Disponibile")
except ImportError:
    dependencies_status["Requests"] = "❌ Non disponibile"
    print("Requests: ❌ Non disponibile")

print("=" * 50)
print("Controllo dipendenze completato!")


# Funzione per verificare se tutte le dipendenze critiche sono disponibili
def check_critical_dependencies():
    """Verifica se le dipendenze critiche sono disponibili."""
    critical_deps = ["PyQt6", "OpenCV", "NumPy", "Pillow"]
    missing = []

    for dep in critical_deps:
        if dependencies_status.get(dep) == "❌ Non disponibile":
            missing.append(dep)

    return missing


if __name__ == "__main__":
    missing = check_critical_dependencies()
    if missing:
        print(f"⚠️  Dipendenze critiche mancanti: {', '.join(missing)}")
        print("💡 Installa con: pip install <nome_dipendenza>")
    else:
        print("✅ Tutte le dipendenze critiche sono disponibili!")
