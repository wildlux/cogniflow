"""
Ollama integration module for DSA Assistant
"""

from .ollama_manager import OllamaManager, OllamaThread, OllamaModelsThread

# Import del bridge
try:
    from .ollama_bridge import OllamaBridge, register_bridge
    _bridge_available = True
except ImportError:
    _bridge_available = False
    OllamaBridge = None
    register_bridge = None

__all__ = ['OllamaManager', 'OllamaThread', 'OllamaModelsThread']

if _bridge_available:
    __all__.extend(['OllamaBridge', 'register_bridge'])