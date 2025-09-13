#!/usr/bin/env python3
"""
Lazy Loader - Caricamento pigro dei moduli per ottimizzazione performance
"""

import importlib
import importlib.util
import sys
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LazyLoader:
    """Caricatore lazy per moduli pesanti con caching intelligente."""

    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._module_specs: Dict[str, Dict[str, Any]] = {
            # Moduli pesanti da caricare lazy
            'cv2': {
                'module': 'cv2',
                'description': 'OpenCV per visione artificiale',
                'heavy': True
            },
            'PIL': {
                'module': 'PIL',
                'description': 'Pillow per processamento immagini',
                'heavy': True
            },
            'numpy': {
                'module': 'numpy',
                'description': 'NumPy per calcolo scientifico',
                'heavy': True
            },
            'PyQt6.QtMultimedia': {
                'module': 'PyQt6.QtMultimedia',
                'description': 'PyQt6 Multimedia per audio/video',
                'heavy': True
            },
            'torch': {
                'module': 'torch',
                'description': 'PyTorch per AI/ML',
                'heavy': True
            },
            'transformers': {
                'module': 'transformers',
                'description': 'HuggingFace Transformers',
                'heavy': True
            },
            'vosk': {
                'module': 'vosk',
                'description': 'Vosk per riconoscimento vocale',
                'heavy': True
            },
            'pytesseract': {
                'module': 'pytesseract',
                'description': 'Tesseract OCR',
                'heavy': True
            }
        }

    def load_module(self, module_name: str) -> Optional[Any]:
        """Carica un modulo in modo lazy con caching."""
        # Controlla cache prima
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]

        # Ottieni specifiche del modulo
        spec = self._module_specs.get(module_name)
        if not spec:
            # Modulo non conosciuto, prova import normale
            try:
                module = importlib.import_module(module_name)
                self._loaded_modules[module_name] = module
                return module
            except ImportError:
                logger.warning(f"Modulo {module_name} non disponibile")
                return None

        # Carica modulo pesante con logging
        try:
            logger.info(f"🔄 Caricamento lazy: {spec['description']}")
            module = importlib.import_module(spec['module'])
            self._loaded_modules[module_name] = module
            logger.info(f"✅ Modulo {module_name} caricato con successo")
            return module
        except ImportError as e:
            logger.warning(f"❌ Modulo {module_name} non disponibile: {e}")
            # Salva None in cache per evitare retry
            self._loaded_modules[module_name] = None
            return None
        except Exception as e:
            logger.error(f"❌ Errore caricamento {module_name}: {e}")
            self._loaded_modules[module_name] = None
            return None

    def is_module_available(self, module_name: str) -> bool:
        """Verifica se un modulo è disponibile senza caricarlo."""
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name] is not None

        # Controlla se il modulo può essere importato
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except Exception:
            return False

    def preload_critical_modules(self):
        """Precarica moduli critici all'avvio."""
        critical_modules = ['numpy', 'PIL']  # Moduli leggeri ma usati frequentemente

        for module_name in critical_modules:
            if self.is_module_available(module_name):
                self.load_module(module_name)
                logger.info(f"📦 Modulo critico precaricato: {module_name}")

    def get_module_info(self) -> Dict[str, Dict[str, Any]]:
        """Restituisce informazioni sui moduli caricati."""
        info = {}
        for name, module in self._loaded_modules.items():
            spec = self._module_specs.get(name, {})
            info[name] = {
                'loaded': module is not None,
                'description': spec.get('description', 'Modulo sconosciuto'),
                'heavy': spec.get('heavy', False)
            }
        return info

    def unload_module(self, module_name: str):
        """Scarica un modulo dalla cache (per liberare memoria)."""
        if module_name in self._loaded_modules:
            # Nota: In Python non è possibile "scaricare" completamente un modulo
            # una volta importato, ma possiamo rimuoverlo dalla nostra cache
            del self._loaded_modules[module_name]
            logger.info(f"🗑️ Modulo rimosso dalla cache: {module_name}")


# Istanza globale del lazy loader
lazy_loader = LazyLoader()


def lazy_import(module_name: str) -> Any:
    """Funzione di comodo per import lazy."""
    return lazy_loader.load_module(module_name)


def is_available(module_name: str) -> bool:
    """Funzione di comodo per verificare disponibilità modulo."""
    return lazy_loader.is_module_available(module_name)


# Inizializzazione all'import
def initialize_lazy_loading():
    """Inizializza il sistema di lazy loading."""
    logger.info("🚀 Inizializzazione lazy loading system")
    lazy_loader.preload_critical_modules()

    # Log moduli disponibili
    available_count = sum(1 for name in lazy_loader._module_specs.keys()
                         if lazy_loader.is_module_available(name))
    total_count = len(lazy_loader._module_specs)

    logger.info(f"📊 Moduli disponibili: {available_count}/{total_count}")

    # Log moduli pesanti disponibili
    heavy_modules = [name for name, spec in lazy_loader._module_specs.items()
                    if spec.get('heavy', False) and lazy_loader.is_module_available(name)]
    if heavy_modules:
        logger.info(f"⚡ Moduli pesanti disponibili: {', '.join(heavy_modules)}")


# Auto-inizializzazione quando il modulo viene importato
if __name__ != '__main__':
    initialize_lazy_loading()