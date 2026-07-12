#!/usr/bin/env python3
"""
VLM Manager - Gestione Vision Language Models per CogniFlow
Sostituisce MediaPipe con modelli VLM basati su Ollama
"""

import os
import sys
import json
import base64
import logging
import threading
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import cv2
import numpy as np

# Import Ollama bridge esistente
try:
    from Artificial_Intelligence.Ollama.ollama_bridge import OllamaBridge
except ImportError:
    OllamaBridge = None


class VLMManager:
    """
    Gestore per Vision Language Models basato su Ollama
    Fornisce funzionalità di riconoscimento gesture, OCR avanzato e analisi immagini
    """

    def __init__(self, model_name: str = "llava-phi3"):
        self.model_name = model_name
        self.ollama_bridge = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)

        # Configurazioni per gesture recognition
        self.gesture_history = []
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  # secondi

        # Configurazioni per OCR
        self.ocr_cache = {}
        self.last_ocr_time = 0
        self.ocr_cooldown = 1.0  # secondi

        # Stati di tracking
        self.face_tracking_enabled = False
        self.hand_tracking_enabled = False
        self.gesture_recognition_enabled = False
        self.human_detection_enabled = False

        # Callback per risultati
        self.on_gesture_detected = None
        self.on_face_detected = None
        self.on_hand_detected = None
        self.on_human_detected = None
        self.on_ocr_result = None

        # Inizializza il bridge Ollama
        self._initialize_bridge()

    def _initialize_bridge(self):
        """Inizializza il bridge Ollama per il VLM"""
        try:
            if OllamaBridge:
                self.ollama_bridge = OllamaBridge()
                self.is_initialized = True
                self.logger.info(
                    f"✅ VLM Manager inizializzato con modello: {self.model_name}"
                )
            else:
                self.logger.error("❌ OllamaBridge non disponibile")
                self.is_initialized = False
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione VLM Manager: {e}")
            self.is_initialized = False

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analizza un frame della webcam usando il VLM

        Args:
            frame: Frame OpenCV (BGR)

        Returns:
            Dict con risultati dell'analisi
        """
        if not self.is_initialized or not self.ollama_bridge:
            return {"error": "VLM Manager non inizializzato"}

        try:
            # Converti frame in base64 per Ollama
            frame_b64 = self._frame_to_base64(frame)

            results = {
                "timestamp": datetime.now().isoformat(),
                "faces": [],
                "hands": [],
                "gestures": [],
                "humans": [],
                "ocr_text": "",
                "analysis": {},
            }

            # Analizza gesture se abilitato
            if self.gesture_recognition_enabled:
                gesture_result = self._analyze_gesture(frame, frame_b64)
                if gesture_result:
                    results["gestures"].append(gesture_result)

            # Analizza volti se abilitato
            if self.face_tracking_enabled:
                face_result = self._analyze_faces(frame, frame_b64)
                if face_result:
                    results["faces"].extend(face_result)

            # Analizza mani se abilitato
            if self.hand_tracking_enabled:
                hand_result = self._analyze_hands(frame, frame_b64)
                if hand_result:
                    results["hands"].extend(hand_result)

            # Analizza umani se abilitato
            if self.human_detection_enabled:
                human_result = self._analyze_humans(frame, frame_b64)
                if human_result:
                    results["humans"].extend(human_result)

            return results

        except Exception as e:
            self.logger.error(f"❌ Errore analisi frame: {e}")
            return {"error": str(e)}

    def _analyze_gesture(
        self, frame: np.ndarray, frame_b64: str
    ) -> Optional[Dict[str, Any]]:
        """Analizza gesture nel frame usando VLM"""
        try:
            # Evita analisi troppo frequenti
            current_time = time.time()
            if current_time - self.last_gesture_time < self.gesture_cooldown:
                return None

            prompt = """
            Analizza questa immagine e identifica eventuali gesture delle mani.
            Descrivi:
            1. Se vedi mani nell'immagine
            2. Che tipo di gesto stanno facendo (pollice su, OK, pugno chiuso, mano aperta, etc.)
            3. La posizione approssimativa delle mani
            4. La confidenza della tua identificazione

            Rispondi in formato JSON con chiavi: gesture, confidence, position, description
            """

            response = self._query_vlm(prompt, frame_b64)
            if response:
                gesture_data = self._parse_gesture_response(response)
                if gesture_data:
                    self.last_gesture_time = current_time
                    self.gesture_history.append(gesture_data)

                    # Mantieni solo le ultime 10 gesture
                    if len(self.gesture_history) > 10:
                        self.gesture_history.pop(0)

                    # Chiama callback se presente
                    if self.on_gesture_detected:
                        self.on_gesture_detected(gesture_data)

                    return gesture_data

        except Exception as e:
            self.logger.error(f"❌ Errore analisi gesture: {e}")

        return None

    def _analyze_faces(self, frame: np.ndarray, frame_b64: str) -> List[Dict[str, Any]]:
        """Analizza volti nel frame usando VLM"""
        try:
            prompt = """
            Analizza questa immagine e identifica eventuali volti umani.
            Per ogni volto trovato, fornisci:
            1. Posizione approssimativa (sinistra, centro, destra)
            2. Età approssimativa
            3. Genere (se riconoscibile)
            4. Espressione facciale
            5. Confidenza dell'identificazione

            Rispondi in formato JSON array di oggetti con chiavi: position, age, gender, expression, confidence
            """

            response = self._query_vlm(prompt, frame_b64)
            if response:
                faces = self._parse_faces_response(response)
                if faces and self.on_face_detected:
                    for face in faces:
                        self.on_face_detected(face)
                return faces

        except Exception as e:
            self.logger.error(f"❌ Errore analisi volti: {e}")

        return []

    def _analyze_hands(self, frame: np.ndarray, frame_b64: str) -> List[Dict[str, Any]]:
        """Analizza mani nel frame usando VLM"""
        try:
            prompt = """
            Analizza questa immagine e identifica eventuali mani.
            Per ogni mano trovata, fornisci:
            1. Posizione approssimativa (coordinate x,y normalizzate 0-1)
            2. Mano sinistra o destra
            3. Tipo di gesto (aperta, chiusa, pollice su, etc.)
            4. Confidenza dell'identificazione

            Rispondi in formato JSON array di oggetti con chiavi: position, hand_type, gesture, confidence
            """

            response = self._query_vlm(prompt, frame_b64)
            if response:
                hands = self._parse_hands_response(response)
                if hands and self.on_hand_detected:
                    for hand in hands:
                        self.on_hand_detected(hand)
                return hands

        except Exception as e:
            self.logger.error(f"❌ Errore analisi mani: {e}")

        return []

    def _analyze_humans(
        self, frame: np.ndarray, frame_b64: str
    ) -> List[Dict[str, Any]]:
        """Analizza presenza umana nel frame usando VLM"""
        try:
            prompt = """
            Analizza questa immagine e identifica eventuali persone.
            Fornisci informazioni su:
            1. Numero di persone visibili
            2. Posizione approssimativa di ciascuna
            3. Attività che stanno svolgendo (se riconoscibile)
            4. Distanza approssimativa dalla camera

            Rispondi in formato JSON con chiave 'humans' contenente array di oggetti
            """

            response = self._query_vlm(prompt, frame_b64)
            if response:
                humans = self._parse_humans_response(response)
                if humans and self.on_human_detected:
                    for human in humans:
                        self.on_human_detected(human)
                return humans

        except Exception as e:
            self.logger.error(f"❌ Errore analisi umani: {e}")

        return []

    def perform_ocr(
        self, image_path: Optional[str] = None, frame: Optional[np.ndarray] = None
    ) -> str:
        """
        Esegue OCR avanzato usando VLM

        Args:
            image_path: Percorso al file immagine
            frame: Frame OpenCV alternativo al file

        Returns:
            Testo estratto dall'immagine
        """
        if not self.is_initialized:
            return "VLM Manager non inizializzato"

        try:
            # Evita OCR troppo frequenti
            current_time = time.time()
            if current_time - self.last_ocr_time < self.ocr_cooldown:
                return "OCR in cooldown"

            # Prepara immagine
            if image_path:
                # Carica immagine da file
                image = cv2.imread(image_path)
                if image is None:
                    return "Impossibile caricare immagine"
            elif frame is not None:
                image = frame.copy()
            else:
                return "Nessuna immagine fornita"

            # Converti in base64
            image_b64 = self._frame_to_base64(image)

            prompt = """
            Analizza questa immagine e estrai tutto il testo visibile.
            Istruzioni:
            1. Leggi tutto il testo presente nell'immagine
            2. Mantieni la formattazione e la struttura originale
            3. Correggi eventuali errori di OCR
            4. Se ci sono più colonne o sezioni, mantieni la struttura
            5. Indica la lingua del testo se riconoscibile

            Fornisci solo il testo estratto, senza commenti aggiuntivi.
            """

            response = self._query_vlm(prompt, image_b64)
            if response:
                self.last_ocr_time = current_time

                # Cache risultato
                cache_key = image_path or "frame"
                self.ocr_cache[cache_key] = response

                # Chiama callback se presente
                if self.on_ocr_result:
                    self.on_ocr_result(response)

                return response

        except Exception as e:
            self.logger.error(f"❌ Errore OCR: {e}")
            return f"Errore OCR: {str(e)}"

        return "Nessun testo rilevato"

    def _query_vlm(self, prompt: str, image_b64: str) -> Optional[str]:
        """Interroga il VLM con prompt e immagine"""
        if not self.ollama_bridge:
            return None

        try:
            # Usa il metodo esistente del bridge Ollama
            # Per ora simuliamo una chiamata - dovremo implementare la chiamata reale
            # quando il bridge Ollama supporterà immagini

            # Simula latenza di processing
            time.sleep(0.1)

            # Mock responses basate sul tipo di prompt
            if "gesture" in prompt.lower():
                return '{"gesture": "Open Hand", "confidence": 0.85, "position": "center", "description": "Mano aperta rilevata"}'
            elif "face" in prompt.lower():
                return '[{"position": "center", "age": "25-35", "gender": "unknown", "expression": "neutral", "confidence": 0.75}]'
            elif "hand" in prompt.lower():
                return '[{"position": {"x": 0.5, "y": 0.5}, "hand_type": "right", "gesture": "open", "confidence": 0.8}]'
            elif "human" in prompt.lower():
                return '{"humans": [{"position": "center", "activity": "standing", "distance": "medium", "confidence": 0.9}]}'
            else:
                return "Testo estratto dall'immagine usando VLM"

        except Exception as e:
            self.logger.error(f"❌ Errore query VLM: {e}")

        return None

    def _frame_to_base64(self, frame: np.ndarray) -> str:
        """Converte frame OpenCV in base64 per Ollama"""
        try:
            # Converti BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Codifica come JPEG
            success, buffer = cv2.imencode(".jpg", frame_rgb)
            if success:
                return base64.b64encode(buffer).decode("utf-8")

        except Exception as e:
            self.logger.error(f"❌ Errore conversione frame: {e}")

        return ""

    def _parse_gesture_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parsa risposta gesture dal VLM"""
        try:
            # Cerca di estrarre JSON dalla risposta
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                return {
                    "gesture": data.get("gesture", "unknown"),
                    "confidence": data.get("confidence", 0.5),
                    "position": data.get("position", "center"),
                    "description": data.get("description", ""),
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"❌ Errore parsing gesture: {e}")

        return None

    def _parse_faces_response(self, response: str) -> List[Dict[str, Any]]:
        """Parsa risposta volti dal VLM"""
        try:
            # Cerca JSON nella risposta
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                faces = json.loads(json_str)

                return [
                    {
                        "position": face.get("position", "unknown"),
                        "age": face.get("age", "unknown"),
                        "gender": face.get("gender", "unknown"),
                        "expression": face.get("expression", "neutral"),
                        "confidence": face.get("confidence", 0.5),
                        "timestamp": datetime.now().isoformat(),
                    }
                    for face in faces
                ]

        except Exception as e:
            self.logger.error(f"❌ Errore parsing faces: {e}")

        return []

    def _parse_hands_response(self, response: str) -> List[Dict[str, Any]]:
        """Parsa risposta mani dal VLM"""
        try:
            # Cerca JSON nella risposta
            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                hands = json.loads(json_str)

                return [
                    {
                        "position": hand.get("position", {"x": 0.5, "y": 0.5}),
                        "hand_type": hand.get("hand_type", "unknown"),
                        "gesture": hand.get("gesture", "unknown"),
                        "confidence": hand.get("confidence", 0.5),
                        "timestamp": datetime.now().isoformat(),
                    }
                    for hand in hands
                ]

        except Exception as e:
            self.logger.error(f"❌ Errore parsing hands: {e}")

        return []

    def _parse_humans_response(self, response: str) -> List[Dict[str, Any]]:
        """Parsa risposta umani dal VLM"""
        try:
            # Cerca JSON nella risposta
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                humans = data.get("humans", [])
                return [
                    {
                        "position": human.get("position", "unknown"),
                        "activity": human.get("activity", "unknown"),
                        "distance": human.get("distance", "unknown"),
                        "confidence": human.get("confidence", 0.5),
                        "timestamp": datetime.now().isoformat(),
                    }
                    for human in humans
                ]

        except Exception as e:
            self.logger.error(f"❌ Errore parsing humans: {e}")

        return []

    # Metodi di controllo stato
    def enable_face_tracking(self):
        """Abilita tracking volti"""
        self.face_tracking_enabled = True
        self.logger.info("✅ Face tracking abilitato")

    def disable_face_tracking(self):
        """Disabilita tracking volti"""
        self.face_tracking_enabled = False
        self.logger.info("❌ Face tracking disabilitato")

    def enable_hand_tracking(self):
        """Abilita tracking mani"""
        self.hand_tracking_enabled = True
        self.logger.info("✅ Hand tracking abilitato")

    def disable_hand_tracking(self):
        """Disabilita tracking mani"""
        self.hand_tracking_enabled = False
        self.logger.info("❌ Hand tracking disabilitato")

    def enable_gesture_recognition(self):
        """Abilita riconoscimento gesture"""
        self.gesture_recognition_enabled = True
        self.logger.info("✅ Gesture recognition abilitato")

    def disable_gesture_recognition(self):
        """Disabilita riconoscimento gesture"""
        self.gesture_recognition_enabled = False
        self.logger.info("❌ Gesture recognition disabilitato")

    def enable_human_detection(self):
        """Abilita rilevamento umani"""
        self.human_detection_enabled = True
        self.logger.info("✅ Human detection abilitato")

    def disable_human_detection(self):
        """Disabilita rilevamento umani"""
        self.human_detection_enabled = False
        self.logger.info("❌ Human detection disabilitato")

    def get_status(self) -> Dict[str, Any]:
        """Restituisce lo stato corrente del VLM Manager"""
        return {
            "initialized": self.is_initialized,
            "model_name": self.model_name,
            "face_tracking": self.face_tracking_enabled,
            "hand_tracking": self.hand_tracking_enabled,
            "gesture_recognition": self.gesture_recognition_enabled,
            "human_detection": self.human_detection_enabled,
            "gesture_history_count": len(self.gesture_history),
            "ocr_cache_count": len(self.ocr_cache),
        }

    def cleanup(self):
        """Pulisce risorse del VLM Manager"""
        try:
            self.gesture_history.clear()
            self.ocr_cache.clear()

            if self.ollama_bridge:
                # Cleanup del bridge se necessario
                pass

            self.logger.info("✅ VLM Manager cleanup completato")

        except Exception as e:
            self.logger.error(f"❌ Errore cleanup VLM Manager: {e}")


# Istanza globale del VLM Manager
vlm_manager = VLMManager()


def get_vlm_manager() -> VLMManager:
    """Restituisce l'istanza globale del VLM Manager"""
    return vlm_manager
