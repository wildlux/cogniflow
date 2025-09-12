#!/usr/bin/env python3
"""
Test script per verificare la struttura refactored
"""

import sys
import os

# Aggiungi il percorso del progetto al PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test degli import dei moduli refactored"""
    print("🔍 Test degli import...")

    try:
        # Test modelli
        from models.project_model import ProjectModel
        from models.settings_model import SettingsModel
        print("✅ Modelli importati correttamente")

        # Test servizi
        from services.ai_service import AIService
        from services.tts_service import TTSService
        from services.speech_recognition_service import SpeechRecognitionService
        from services.ocr_service import OCRService
        from services.media_service import MediaService
        from services.project_service import ProjectService
        print("✅ Servizi importati correttamente")

        # Test controller
        from controllers.cogniflow_controller import CogniFlowController
        print("✅ Controller importato correttamente")

        # Test UI refactored
        from UI.main_window_refactored import MainWindowRefactored, UIManager
        print("✅ UI refactored importata correttamente")

        return True

    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

def test_models():
    """Test dei modelli"""
    print("\n🔍 Test dei modelli...")

    try:
        from models.project_model import ProjectModel
        from models.settings_model import SettingsModel

        # Test ProjectModel
        project = ProjectModel("Test Project", {"test": "data"})
        assert project.name == "Test Project"
        assert project.data["test"] == "data"
        print("✅ ProjectModel funziona correttamente")

        # Test SettingsModel
        settings = SettingsModel()
        settings.set("test.key", "value")
        assert settings.get("test.key") == "value"
        print("✅ SettingsModel funziona correttamente")

        return True

    except Exception as e:
        print(f"❌ Errore test modelli: {e}")
        return False

def test_services():
    """Test dei servizi"""
    print("\n🔍 Test dei servizi...")

    try:
        from services.ai_service import AIService
        from services.project_service import ProjectService

        # Test AI Service
        ai_service = AIService()
        assert hasattr(ai_service, 'send_request')
        assert hasattr(ai_service, 'is_available')
        print("✅ AIService inizializzato correttamente")

        # Test Project Service
        project_service = ProjectService()
        assert hasattr(project_service, 'save_project')
        assert hasattr(project_service, 'load_project')
        print("✅ ProjectService inizializzato correttamente")

        return True

    except Exception as e:
        print(f"❌ Errore test servizi: {e}")
        return False

def test_controller():
    """Test del controller"""
    print("\n🔍 Test del controller...")

    try:
        from controllers.cogniflow_controller import CogniFlowController

        controller = CogniFlowController()
        assert hasattr(controller, 'send_ai_request')
        assert hasattr(controller, 'save_project')
        assert hasattr(controller, 'get_status_info')
        print("✅ Controller inizializzato correttamente")

        # Test metodi del controller
        status = controller.get_status_info()
        assert isinstance(status, dict)
        assert 'services_status' in status
        print("✅ Metodi del controller funzionano correttamente")

        return True

    except Exception as e:
        print(f"❌ Errore test controller: {e}")
        return False

def test_ui_manager():
    """Test dell'UI Manager"""
    print("\n🔍 Test dell'UI Manager...")

    try:
        from PyQt6.QtWidgets import QApplication
        from UI.main_window_refactored import UIManager

        # Crea applicazione Qt se non esiste
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Nota: Non possiamo testare completamente l'UI senza una finestra
        # ma possiamo verificare che la classe sia importabile
        print("✅ UI Manager importato correttamente (test completo richiede GUI)")

        return True

    except Exception as e:
        print(f"❌ Errore test UI Manager: {e}")
        return False

def main():
    """Funzione principale di test"""
    print("🚀 Avvio test struttura refactored CogniFlow")
    print("=" * 50)

    results = []

    # Test import
    results.append(("Import", test_imports()))

    # Test componenti
    results.append(("Modelli", test_models()))
    results.append(("Servizi", test_services()))
    results.append(("Controller", test_controller()))
    results.append(("UI Manager", test_ui_manager()))

    # Riepilogo
    print("\n" + "=" * 50)
    print("📊 RIEPILOGO TEST:")

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSATO" if success else "❌ FALLITO"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1

    print(f"\n🎯 Risultato: {passed}/{total} test passati")

    if passed == total:
        print("🎉 Tutti i test sono passati! La struttura refactored è funzionante.")
        return 0
    else:
        print("⚠️ Alcuni test sono falliti. Verifica gli errori sopra.")
        return 1

if __name__ == "__main__":
    sys.exit(main())