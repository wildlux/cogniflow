# vision_language_detector.py
# Classe semplificata per l'integrazione di Vision-Language Models (VLMs) come LLaVA

import base64
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import json

# Configurazione logging
logger = logging.getLogger(__name__)


class VisionLanguageDetector:
    """
    Classe semplificata per l'integrazione di Vision-Language Models (VLMs).
    Sostituisce MediaPipe con LLaVA per funzionalità più potenti e semplici.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = ollama_url
        self.cache = {}
        self.cache_timeout = 1.0

        # Prompt ottimizzati per diversi task
        self.prompts = {
            "face_detection": """
Analizza questa immagine e descrivi:
1. Numero di facce visibili
2. Posizione approssimativa di ogni faccia (sinistra, centro, destra)
3. Espressione di ogni volto (felice, triste, neutra, sorpresa, arrabbiata)
4. Età approssimativa di ogni persona

Rispondi in formato JSON con questa struttura:
{
  "faces_detected": numero,
  "faces": [
    {
      "position": "sinistra|centro|destra",
      "expression": "felice|triste|neutra|sorpresa|arrabbiata",
      "age_range": "bambino|giovane|adulto|anziano"
    }
  ]
}
""",
            "hand_detection": """
Analizza questa immagine e identifica le mani:
1. Numero di mani visibili
2. Mano destra o sinistra per ciascuna
3. Posizione approssimativa (sinistra, centro, destra del frame)
4. Gesto che sta facendo ogni mano (aperta, chiusa, pollice su, etc.)

Rispondi in formato JSON:
{
  "hands_detected": numero,
  "hands": [
    {
      "hand_type": "left|right",
      "position": "left|center|right",
      "gesture": "open_hand|closed_hand|thumbs_up|pointing|other"
    }
  ]
}
""",
            "pose_detection": """
Descrivi la posa delle persone in questa immagine:
1. Numero di persone visibili
2. Posizione del corpo (in piedi, seduto, sdraiato)
3. Orientamento (di fronte, di spalle, di lato)

Rispondi in formato JSON:
{
  "persons_detected": numero,
  "poses": [
    {
      "position": "standing|sitting|lying",
      "orientation": "front|back|side"
    }
  ]
}
""",
            "gesture_recognition": """
Analizza i gesti delle mani in questa immagine:
1. Identifica tutti i gesti specifici (pollice su, ok, pace, pugno, etc.)
2. Determina se i gesti sono rivolti alla telecamera

Rispondi in formato JSON:
{
  "gestures_detected": numero,
  "gestures": [
    {
      "gesture_type": "thumbs_up|ok_sign|peace_sign|fist|pointing|wave|other",
      "direction": "towards_camera|away|sideways"
    }
  ]
}
""",
            "human_detection": """
Rileva la presenza umana in questa immagine:
1. Numero di persone visibili
2. Posizione approssimativa di ciascuna persona

Rispondi in formato JSON:
{
  "humans_detected": numero,
  "detections": [
    {
      "position": "left|center|right"
    }
  ]
}
""",
        }

    def is_available(self) -> bool:
        """Verifica se il sistema VLM è disponibile"""
        try:
            # Test semplice di connessione a Ollama
            import requests

            response = requests.get(f"{self.ollama_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False

    def frame_to_base64(self, frame) -> str:
        """Converte un frame in base64 per LLaVA"""
        try:
            import cv2

            # Converti in JPEG e poi base64
            success, buffer = cv2.imencode(".jpg", frame)
            if success:
                frame_bytes = buffer.tobytes()
                return base64.b64encode(frame_bytes).decode("utf-8")
            return ""
        except:
            return ""

    async def analyze_frame(self, frame, task: str = "general") -> Dict[str, Any]:
        """
        Analizza un frame usando VLM per il task specificato
        """
        if not self.is_available():
            return self._fallback_analysis(frame, task)

        try:
            # Converti frame in base64
            image_b64 = self.frame_to_base64(frame)
            if not image_b64:
                return self._fallback_analysis(frame, task)

            # Seleziona prompt
            prompt = self.prompts.get(
                f"{task}_detection", self.prompts["human_detection"]
            )

            # Chiama LLaVA
            result = await self._call_llava(prompt, image_b64, task)

            if result:
                return result
            else:
                return self._fallback_analysis(frame, task)

        except Exception as e:
            self.logger.error(f"Errore analisi VLM: {e}")
            return self._fallback_analysis(frame, task)

    async def _call_llava(
        self, prompt: str, image_b64: str, task: str
    ) -> Dict[str, Any]:
        """Chiama LLaVA tramite Ollama"""
        try:
            import requests

            payload = {
                "model": "llava:7b",
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {"temperature": 0.1, "max_tokens": 300},
            }

            response = requests.post(
                f"{self.ollama_url}/api/generate", json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")

                # Parse JSON dalla risposta
                result = self._parse_llava_response(response_text, task)
                return result if result else self._fallback_analysis(None, task)
            else:
                self.logger.warning(f"LLaVA API error: {response.status_code}")
                return self._fallback_analysis(None, task)

        except Exception as e:
            self.logger.error(f"Errore chiamata LLaVA: {e}")
            return {"error": "LLaVA call failed", "task": task, "method": "error"}

    def _parse_llava_response(self, response: str, task: str) -> Dict[str, Any]:
        """Parse la risposta di LLaVA"""
        try:
            # Cerca JSON nella risposta
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)

                # Aggiungi metadati
                parsed["task"] = task
                parsed["timestamp"] = datetime.now().isoformat()
                parsed["method"] = "vlm_llava"

                return parsed
            else:
                # Fallback: estrai info testuali
                return self._parse_text_response(response, task)

        except:
            return self._parse_text_response(response, task)

    def _parse_text_response(self, response: str, task: str) -> Dict[str, Any]:
        """Parse risposte testuali"""
        result = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "method": "vlm_llava_text",
            "raw_response": response,
        }

        # Estrai numeri dalla risposta
        response_lower = response.lower()

        if "face" in task:
            face_count = response_lower.count("face") + response_lower.count("person")
            result["faces_detected"] = str(face_count)
        elif "hand" in task:
            hand_count = response_lower.count("hand") + response_lower.count("mano")
            result["hands_detected"] = str(hand_count)
        elif "human" in task:
            human_count = response_lower.count("person") + response_lower.count("human")
            result["humans_detected"] = str(human_count)

        return result

    def _fallback_analysis(self, frame, task: str) -> Dict[str, Any]:
        """Fallback semplice quando VLM non è disponibile"""
        result = {
            "task": task,
            "method": "fallback",
            "timestamp": datetime.now().isoformat(),
            "error": "VLM not available",
        }

        # Fallback molto semplice basato su dimensione frame
        if hasattr(frame, "shape") and frame is not None:
            height, width = frame.shape[:2]
            # Simula rilevamento basato su dimensione immagine
            if task == "face":
                result["faces_detected"] = "1" if width > 640 else "0"
            elif task == "hand":
                result["hands_detected"] = "1" if height > 480 else "0"
            elif task == "human":
                result["humans_detected"] = "1" if width * height > 300000 else "0"

        return result

    # Metodi di convenienza
    async def detect_faces(self, frame) -> Dict[str, Any]:
        """Rilevamento facce"""
        return await self.analyze_frame(frame, "face")

    async def detect_hands(self, frame) -> Dict[str, Any]:
        """Rilevamento mani"""
        return await self.analyze_frame(frame, "hand")

    async def detect_poses(self, frame) -> Dict[str, Any]:
        """Rilevamento pose"""
        return await self.analyze_frame(frame, "pose")

    async def recognize_gestures(self, frame) -> Dict[str, Any]:
        """Riconoscimento gesti"""
        return await self.analyze_frame(frame, "gesture")

    async def detect_humans(self, frame) -> Dict[str, Any]:
        """Rilevamento umani"""
        return await self.analyze_frame(frame, "human")

    def get_system_status(self) -> Dict[str, Any]:
        """Stato del sistema VLM"""
        return {
            "vlm_available": self.is_available(),
            "ollama_url": self.ollama_url,
            "cache_size": len(self.cache),
            "supported_tasks": list(self.prompts.keys()),
        }


# Istanza globale
vision_detector = VisionLanguageDetector()
