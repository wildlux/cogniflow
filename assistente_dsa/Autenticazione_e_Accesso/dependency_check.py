"""Controllo delle librerie necessarie prima dell'avvio del software.

Usato dalla schermata di login per mostrare all'utente lo stato delle
dipendenze PRIMA di entrare nell'applicazione. Il controllo usa
``importlib.util.find_spec`` (verifica la presenza del pacchetto senza
importarlo davvero), quindi è quasi istantaneo anche con librerie pesanti
come OpenCV o MediaPipe; i programmi di sistema sono cercati nel PATH.
"""

import importlib.util
import shutil

# (nome visibile, modulo python, critica?, a cosa serve, come installarla)
PYTHON_DEPS = [
    ("PyQt6", "PyQt6", True, "interfaccia grafica", "pip install PyQt6"),
    ("OpenCV", "cv2", True, "webcam e visione", "pip install opencv-python"),
    ("NumPy", "numpy", True, "calcolo numerico", "pip install numpy"),
    ("Pillow", "PIL", True, "gestione immagini", "pip install Pillow"),
    ("Requests", "requests", True, "rete e AI", "pip install requests"),
    ("cryptography", "cryptography", True, "credenziali cifrate",
     "pip install cryptography"),
    ("psutil", "psutil", False, "monitor di sistema", "pip install psutil"),
    ("pytesseract", "pytesseract", False, "OCR scrittura a mano",
     "pip install pytesseract"),
    ("PyMuPDF", "fitz", False, "lettura PDF", "pip install PyMuPDF"),
    ("argostranslate", "argostranslate", False, "traduzione offline",
     "pip install argostranslate"),
    ("pydub", "pydub", False, "audio per trascrizione", "pip install pydub"),
    ("vosk", "vosk", False, "trascrizione vocale offline", "pip install vosk"),
    ("MediaPipe", "mediapipe", False, "gesti e viso avanzati",
     "pip install mediapipe"),
]

# Programmi esterni cercati nel PATH di sistema
SYSTEM_TOOLS = [
    ("tesseract", "tesseract", False, "motore OCR",
     "sudo apt install tesseract-ocr tesseract-ocr-ita"),
    ("ffmpeg", "ffmpeg", False, "conversione audio",
     "sudo apt install ffmpeg"),
    ("Ollama", "ollama", False, "AI locale", "https://ollama.com/download"),
]


def check_dependencies():
    """Controlla tutte le dipendenze e restituisce l'elenco degli esiti.

    Ritorna una lista di dizionari con chiavi: name, ok, critical,
    purpose, install.
    """
    results = []
    for name, module, critical, purpose, install in PYTHON_DEPS:
        try:
            ok = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            ok = False
        results.append({
            "name": name, "ok": ok, "critical": critical,
            "purpose": purpose, "install": install,
        })
    for name, binary, critical, purpose, install in SYSTEM_TOOLS:
        results.append({
            "name": name, "ok": shutil.which(binary) is not None,
            "critical": critical, "purpose": purpose, "install": install,
        })
    return results


def missing_critical(results):
    """Nomi delle dipendenze critiche mancanti."""
    return [r["name"] for r in results if r["critical"] and not r["ok"]]


def missing_optional(results):
    """Nomi delle dipendenze opzionali mancanti."""
    return [r["name"] for r in results if not r["critical"] and not r["ok"]]


if __name__ == "__main__":
    res = check_dependencies()
    for r in res:
        stato = "✅" if r["ok"] else ("❌" if r["critical"] else "⚠️")
        print(f"{stato} {r['name']:<15} {r['purpose']}"
              + ("" if r["ok"] else f"  →  {r['install']}"))
    crit = missing_critical(res)
    if crit:
        print(f"\n❌ Librerie critiche mancanti: {', '.join(crit)}")
    else:
        print("\n✅ Tutte le librerie critiche sono disponibili")
