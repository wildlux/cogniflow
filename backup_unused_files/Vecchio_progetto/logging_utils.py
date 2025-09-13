# logging_utils.py - Utilità per il logging

import logging
from PyQt6.QtCore import QObject, pyqtSignal


class LogEmitter(QObject):
    new_record = pyqtSignal(str)
    error_occurred = pyqtSignal()


class TextEditLogger(logging.Handler):
    def __init__(self, log_emitter, parent=None):
        super().__init__()
        self.log_emitter = log_emitter
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record):
        msg = self.format(record)
        self.log_emitter.new_record.emit(msg)
        if record.levelno >= logging.ERROR:
            self.log_emitter.error_occurred.emit()

import logging
from PyQt6.QtCore import QObject, pyqtSignal


class LogEmitter(QObject):
    """Oggetto QObject per emettere segnali di log."""

    new_record = pyqtSignal(str)
    error_occurred = pyqtSignal()


class TextEditLogger(logging.Handler):
    """Handler di logging personalizzato che emette segnali a un QTextEdit."""

    def __init__(self, log_emitter, parent=None):
        super().__init__()
        self.log_emitter = log_emitter
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

    def emit(self, record):
        msg = self.format(record)
        self.log_emitter.new_record.emit(msg)
        if record.levelno >= logging.ERROR:
            self.log_emitter.error_occurred.emit()