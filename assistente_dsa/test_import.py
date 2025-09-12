#!/usr/bin/env python3
"""Test script per verificare gli import"""

try:
    from Artificial_Intelligence.Sintesi_Vocale.managers.tts_engine_manager import (
        TTSManager,
    )

    print("✅ TTSManager importato correttamente")
except ImportError as e:
    print(f"❌ Errore import TTSManager: {e}")

try:
    from Artificial_Intelligence.Video.visual_background import VideoThread

    print("✅ VideoThread importato correttamente")
except ImportError as e:
    print(f"❌ Errore import VideoThread: {e}")

try:
    from UI.draggable_text_widget import DraggableTextWidget

    print("✅ DraggableTextWidget importato correttamente")
except ImportError as e:
    print(f"❌ Errore import DraggableTextWidget: {e}")
