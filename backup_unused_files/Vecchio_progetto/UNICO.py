import sys
import threading
import cv2
import json
import logging
import time
from datetime import datetime
import numpy as np
import subprocess
import re
import requests
import base64
import wave
from io import BytesIO

from PyQt6.QtCore import (
    QThread,
    pyqtSignal,
    QTimer,
    Qt,
    QMimeData,
    QPoint,
    QObject,
    QSize,
    QPropertyAnimation,
    QRect,
    QEvent,
    QBuffer,
    QIODevice,
)
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QDrag,
    QCursor,
    QIcon,
    QPainter,
    QPen,
    QColor,
    QMouseEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QFrame,
    QGridLayout,
    QDialog,
    QTextEdit,
    QTabWidget,
    QCheckBox,
    QSlider,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QStackedWidget,
    QScrollArea,
    QSpacerItem,
    QGroupBox,
    QMenu,
)

from ui_style import DRAGGABLE_WIDGET_STYLE, LOG_WIDGET_STYLE, TEXT_INPUT_STYLE, AI_RESULTS_STYLE, get_scrollable_panel_style
from ui_style.main_styles import get_main_stylesheet
from animations import toggle_log_panel_visibility
from Opzioni import ConfigurationDialog
from webcam_manager import VideoThread
from ollama_thread import OllamaThread
from voice_recognition_thread import VoiceRecognitionThread
from tts_thread import TTSThread
from main_window import MainWindow


# ---------------------------------------------------------------------------------
def main():
    """Funzione principale."""
    app = QApplication(sys.argv)
    app.setApplicationName("Assistente per Dislessia")
    app.setOrganizationName("DSA Helper")

    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
