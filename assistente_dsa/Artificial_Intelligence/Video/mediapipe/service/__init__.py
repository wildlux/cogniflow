"""
MediaPipe service module.
"""

try:
    from .mediapipe_service import MediaPipeService
except ImportError:
    MediaPipeService = None

try:
    from .mediapipe_processor import MediaPipeProcessor
except ImportError:
    MediaPipeProcessor = None

__all__ = ['MediaPipeService', 'MediaPipeProcessor']