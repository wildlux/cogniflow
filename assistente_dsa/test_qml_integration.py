#!/usr/bin/env python3
"""
Test script per verificare l'integrazione QML con Ollama
"""


# Aggiungi il percorso per importare i moduli
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "UI"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Artificial_Intelligence"))


def test_ollama_bridge():
    """Test del bridge Ollama"""
    try:
        from Artificial_Intelligence.Ollama import OllamaBridge
        print("✅ Bridge Ollama importato con successo")

        bridge = OllamaBridge()
        connected = bridge.checkConnection()
        if connected:
            print("✅ Ollama è connesso")
        else:
            print("❌ Ollama non è connesso")

        return True
    except ImportError as e:
        print("❌ Errore nell'import del bridge: {e}")
        return False


def test_qml_launch():
    """Test del lancio QML"""
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 QML importato con successo")
        return True
    except ImportError as e:
        print("❌ Errore nell'import PyQt6 QML: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Test Integrazione QML-Ollama")
    print("=" * 40)

    bridge_ok = test_ollama_bridge()
    qml_ok = test_qml_launch()

    if bridge_ok and qml_ok:
        print("\n✅ Tutti i test passati! Puoi avviare l'interfaccia QML.")
        print("💡 Comando: python UI/qml_launcher.py")
    else:
        print("\n❌ Alcuni test sono falliti. Verifica le dipendenze.")
