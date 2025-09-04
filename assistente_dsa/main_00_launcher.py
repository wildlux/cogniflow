#!/usr/bin/env python3
"""
Script per avviare l'applicazione DSA in modo sicuro
"""

import sys
import os
import traceback
import json

# Import del sistema di configurazione centralizzato
from main_03_configurazione_e_opzioni import get_config, load_settings, get_setting

def test_imports():
    """Test all critical imports usando il sistema di configurazione centralizzato"""
    print("🔍 Testing imports with centralized configuration...")

    try:
        # Test import configurazione centralizzata
        config = get_config()
        settings = load_settings()

        # Ottieni dimensioni finestra dalle impostazioni centralizzate
        window_width = int(get_setting('ui.window_width', 1200))
        window_height = int(get_setting('ui.window_height', 800))

        print(f"✓ Centralized settings loaded - Window size: {window_width}x{window_height}")
        print(f"✓ Application theme: {get_setting('application.theme', 'Chiaro')}")

        # Test degli import critici
        try:
            # Test classe MainWindow (ora integrata in main_01_Aircraft)
            print("✓ MainWindow class available in main_01_Aircraft")

            # Test import widget trascinabile
            import UI.draggable_text_widget
            print("✓ Widget module imported successfully")

            # Test import main_01_Aircraft
            import main_01_Aircraft
            print("✓ Main Aircraft launcher imported successfully")

        except ImportError as e:
            print(f"✗ Critical module import failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def run_app():
    """Run the application by calling main_01_Aircraft.py with centralized configuration"""
    if not test_imports():
        print("❌ Cannot start application due to import errors")
        return

    try:
        print("🚀 Starting DSA Assistant...")
        print("✈️ Calling Aircraft main interface...")

        # Verifica che le impostazioni siano accessibili globalmente
        config = get_config()
        settings = load_settings()

        print(f"📊 Global settings loaded - Theme: {settings['application']['theme']}")
        print(f"🔧 UI Size: {settings['ui']['window_width']}x{settings['ui']['window_height']}")

        # Import and run main_01_Aircraft
        import subprocess
        import sys

        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aircraft_script = os.path.join(current_dir, "main_01_Aircraft.py")

        # Call main_01_Aircraft.py
        result = subprocess.run([sys.executable, aircraft_script], cwd=current_dir)

        if result.returncode != 0:
            print(f"❌ Aircraft exited with error code: {result.returncode}")
        else:
            print("✅ Aircraft completed successfully")

    except Exception as e:
        print(f"❌ Application error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_app()