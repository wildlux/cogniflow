#!/usr/bin/env python3
"""
VLM OCR - Riconoscimento Ottico Caratteri Avanzato con VLM
Utilizza Vision Language Models per OCR più accurato e intelligente
"""

import os
import cv2
import numpy as np
import logging
import json
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import VLM Manager
try:
    from .vlm_manager import VLMManager, get_vlm_manager

    VLM_AVAILABLE = True
except ImportError:
    VLM_AVAILABLE = False
    VLMManager = None
    get_vlm_manager = None

# Fallback OCR tradizionale
try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class VLMOCR:
    """
    OCR Avanzato basato su Vision Language Models
    Supporta testo multi-lingua, layout complesso e correzione intelligente
    """

    def __init__(self):
        self.vlm_manager = None
        self.logger = logging.getLogger(__name__)

        # Inizializza VLM Manager
        if VLM_AVAILABLE and get_vlm_manager:
            try:
                self.vlm_manager = get_vlm_manager()
                self.logger.info("✅ VLM OCR inizializzato con VLM Manager")
            except Exception as e:
                self.logger.error(f"❌ Errore inizializzazione VLM Manager: {e}")
                self.vlm_manager = None

        # Configurazioni OCR
        self.supported_languages = [
            "ita",
            "eng",
            "spa",
            "fra",
            "deu",
            "rus",
            "jpn",
            "chi_sim",
        ]
        self.default_language = "ita+eng"

        # Cache risultati
        self.ocr_cache = {}
        self.cache_max_size = 50

    def extract_text(
        self,
        image_path: Optional[str] = None,
        frame: Optional[np.ndarray] = None,
        language: str = "auto",
    ) -> Dict[str, Any]:
        """
        Estrae testo da immagine usando VLM per OCR avanzato

        Args:
            image_path: Percorso al file immagine
            frame: Frame OpenCV alternativo
            language: Lingua del testo ("auto" per rilevamento automatico)

        Returns:
            Dict con testo estratto e metadati
        """
        if not self.vlm_manager:
            return self._fallback_ocr(image_path, frame, language)

        try:
            # Prepara immagine
            if image_path:
                image = cv2.imread(image_path)
                if image is None:
                    return {"error": "Impossibile caricare immagine"}
            elif frame is not None:
                image = frame.copy()
            else:
                return {"error": "Nessuna immagine fornita"}

            # Migliora qualità immagine per OCR
            processed_image = self._preprocess_image(image)

            # Usa VLM per OCR avanzato
            result = self._vlm_ocr(processed_image, language)

            # Aggiungi metadati
            result.update(
                {
                    "timestamp": datetime.now().isoformat(),
                    "method": "vlm",
                    "language": language,
                    "image_shape": image.shape,
                    "confidence": self._estimate_confidence(result.get("text", "")),
                }
            )

            # Cache risultato
            self._cache_result(image_path or "frame", result)

            return result

        except Exception as e:
            self.logger.error(f"❌ Errore VLM OCR: {e}")
            # Fallback a OCR tradizionale
            return self._fallback_ocr(image_path, frame, language)

    def _vlm_ocr(self, image: np.ndarray, language: str) -> Dict[str, Any]:
        """Esegue OCR usando VLM per analisi intelligente"""
        try:
            # Prompt specifico per OCR
            if language == "auto":
                prompt = """
                Analizza questa immagine e estrai tutto il testo visibile.
                Istruzioni dettagliate:
                1. Leggi e trascrivi tutto il testo presente nell'immagine
                2. Mantieni la formattazione originale (capoversi, liste, etc.)
                3. Riconosci la lingua del testo e segnalala
                4. Correggi eventuali errori di digitazione o OCR
                5. Se ci sono colonne multiple o layout complesso, mantieni la struttura
                6. Estrai anche testo da elementi grafici se presente
                7. Fornisci una stima della qualità del testo estratto

                Restituisci un oggetto JSON con:
                - text: il testo estratto completo
                - language: lingua rilevata
                - layout: descrizione del layout (single column, multi-column, etc.)
                - quality: qualità stimata (high, medium, low)
                - corrections: eventuali correzioni apportate
                """
            else:
                prompt = f"""
                Analizza questa immagine e estrai tutto il testo in {language}.
                Istruzioni:
                1. Leggi tutto il testo presente nell'immagine
                2. Mantieni la formattazione originale
                3. Correggi errori specifici della lingua {language}
                4. Mantieni la struttura del documento
                5. Estrai anche testo da grafici o elementi decorativi

                Restituisci il testo estratto completo.
                """

            # Converti immagine in base64
            image_b64 = self._image_to_base64(image)

            # Query VLM
            response = self.vlm_manager._query_vlm(prompt, image_b64)

            if response:
                # Parsa risposta VLM
                return self._parse_vlm_ocr_response(response)
            else:
                return {"text": "", "error": "Nessuna risposta dal VLM"}

        except Exception as e:
            self.logger.error(f"❌ Errore VLM OCR query: {e}")
            return {"text": "", "error": str(e)}

    def _parse_vlm_ocr_response(self, response: str) -> Dict[str, Any]:
        """Parsa risposta OCR dal VLM"""
        try:
            # Cerca JSON nella risposta
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return data
            else:
                # Risposta testuale semplice
                return {
                    "text": response.strip(),
                    "language": "unknown",
                    "layout": "unknown",
                    "quality": "medium",
                    "corrections": [],
                }

        except Exception as e:
            self.logger.error(f"❌ Errore parsing risposta VLM OCR: {e}")
            return {
                "text": response.strip() if response else "",
                "language": "unknown",
                "layout": "unknown",
                "quality": "low",
                "corrections": [],
            }

    def _fallback_ocr(
        self,
        image_path: Optional[str] = None,
        frame: Optional[np.ndarray] = None,
        language: str = "auto",
    ) -> Dict[str, Any]:
        """OCR tradizionale come fallback"""
        try:
            # Prepara immagine
            if image_path:
                image = cv2.imread(image_path)
                if image is None:
                    return {"error": "Impossibile caricare immagine"}
            elif frame is not None:
                image = frame.copy()
            else:
                return {"error": "Nessuna immagine fornita"}

            # Preprocessing
            processed_image = self._preprocess_image(image)

            # Converti a grayscale
            gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)

            # OCR con Tesseract se disponibile
            if TESSERACT_AVAILABLE:
                # Configurazione Tesseract
                config = "--oem 3 --psm 6"

                if language == "auto":
                    lang_config = self.default_language
                else:
                    lang_config = language

                text = pytesseract.image_to_string(
                    gray, lang=lang_config, config=config
                )

                return {
                    "text": text.strip(),
                    "method": "tesseract",
                    "language": lang_config,
                    "layout": "unknown",
                    "quality": "medium",
                    "confidence": self._estimate_confidence(text),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "error": "Né VLM né Tesseract disponibili per OCR",
                    "method": "none",
                    "text": "",
                }

        except Exception as e:
            self.logger.error(f"❌ Errore fallback OCR: {e}")
            return {"error": str(e), "method": "error", "text": ""}

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocessa immagine per migliorare OCR"""
        try:
            # Converti a grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Riduci rumore
            denoised = cv2.medianBlur(gray, 3)

            # Migliora contrasto
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # Binarizzazione adattiva
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Morfologia per pulire rumore
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            self.logger.warning(f"Errore preprocessing: {e}")
            return image

    def _image_to_base64(self, image: np.ndarray) -> str:
        """Converte immagine in base64 per VLM"""
        try:
            # Converti BGR a RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Codifica come JPEG
            success, buffer = cv2.imencode(
                ".jpg", image_rgb, [cv2.IMWRITE_JPEG_QUALITY, 90]
            )
            if success:
                return base64.b64encode(buffer).decode("utf-8")

        except Exception as e:
            self.logger.error(f"❌ Errore conversione immagine: {e}")

        return ""

    def _estimate_confidence(self, text: str) -> float:
        """Stima confidenza del testo estratto"""
        if not text or len(text.strip()) == 0:
            return 0.0

        # Fattori di confidenza
        confidence = 0.5  # Base

        # Lunghezza testo
        text_length = len(text.strip())
        if text_length > 100:
            confidence += 0.2
        elif text_length < 10:
            confidence -= 0.2

        # Presenza caratteri speciali vs alfanumerici
        alpha_count = sum(1 for c in text if c.isalnum())
        special_count = sum(1 for c in text if not c.isalnum() and not c.isspace())

        if alpha_count > 0:
            special_ratio = special_count / alpha_count
            if special_ratio < 0.1:  # Poco rumore
                confidence += 0.2
            elif special_ratio > 0.5:  # Molto rumore
                confidence -= 0.3

        # Linee multiple (probabilmente documento strutturato)
        lines = text.split("\n")
        if len(lines) > 3:
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def _cache_result(self, key: str, result: Dict[str, Any]):
        """Cache risultato OCR"""
        if len(self.ocr_cache) >= self.cache_max_size:
            # Rimuovi elemento più vecchio
            oldest_key = next(iter(self.ocr_cache))
            del self.ocr_cache[oldest_key]

        self.ocr_cache[key] = result

    def get_cached_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Recupera risultato dalla cache"""
        return self.ocr_cache.get(key)

    def clear_cache(self):
        """Pulisce cache OCR"""
        self.ocr_cache.clear()
        self.logger.info("Cache OCR pulita")

    def get_supported_languages(self) -> List[str]:
        """Restituisce lingue supportate"""
        return self.supported_languages.copy()

    def is_available(self) -> bool:
        """Verifica se OCR è disponibile"""
        return (
            self.vlm_manager and self.vlm_manager.is_initialized
        ) or TESSERACT_AVAILABLE

    def get_status(self) -> Dict[str, Any]:
        """Restituisce stato del sistema OCR"""
        return {
            "vlm_available": self.vlm_manager is not None
            and self.vlm_manager.is_initialized,
            "tesseract_available": TESSERACT_AVAILABLE,
            "overall_available": self.is_available(),
            "supported_languages": self.supported_languages,
            "cache_size": len(self.ocr_cache),
            "cache_max_size": self.cache_max_size,
        }


# Istanza globale VLM OCR
vlm_ocr = VLMOCR()


def get_vlm_ocr() -> VLMOCR:
    """Restituisce l'istanza globale del VLM OCR"""
    return vlm_ocr
