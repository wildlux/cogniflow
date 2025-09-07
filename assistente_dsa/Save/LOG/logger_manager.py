# logger_manager.py

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredLogger:
    """
    Sistema di logging strutturato per l'applicazione.

    Caratteristiche:
    - Logging per componenti (video, AI, TTS, UI, etc.)
    - Livelli di log configurabili
    - Rotazione automatica dei file di log
    - Formattazione JSON per log strutturati
    - Console e file logging simultanei
    """

    def __init__(self, log_dir: str = "logs", app_name: str = "AssistenteDSA"):
        """
        Inizializza il sistema di logging strutturato.

        Args:
            log_dir (str): Directory per i file di log
            app_name (str): Nome dell'applicazione
        """
        self.log_dir = log_dir
        self.app_name = app_name
        self.loggers = {}
        self.setup_logging()

    def setup_logging(self):
        """Configura il sistema di logging."""
        # Crea la directory dei log se non esiste
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Configura il logger root
        self.root_logger = logging.getLogger(self.app_name)
        self.root_logger.setLevel(logging.DEBUG)

        # Rimuovi eventuali handler esistenti
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)

        # Handler per console
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self.root_logger.addHandler(console_handler)

        # Handler per file generale
        general_file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, "{self.app_name}.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        general_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
        )
        general_file_handler.setFormatter(general_formatter)
        general_file_handler.setLevel(logging.DEBUG)
        self.root_logger.addHandler(general_file_handler)

        # Handler per errori
        error_file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, "{self.app_name}_error.log"),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n'
            'Traceback: %(exc_info)s\n'
            '---'
        )
        error_file_handler.setFormatter(error_formatter)
        error_file_handler.setLevel(logging.ERROR)
        self.root_logger.addHandler(error_file_handler)

    def get_logger(self, component: str) -> logging.Logger:
        """
        Ottiene un logger per un componente specifico.

        Args:
            component (str): Nome del componente

        Returns:
            logging.Logger: Logger configurato per il componente
        """
        if component in self.loggers:
            return self.loggers[component]

        logger = logging.getLogger("{self.app_name}.{component}")
        self.loggers[component] = logger
        return logger

    def log_event(self, component: str, level: str, message: str,
                  data: Optional[Dict[str, Any]] = None,
                  error: Optional[Exception] = None):
        """
        Logga un evento strutturato.

        Args:
            component (str): Componente che genera l'evento
            level (str): Livello di log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message (str): Messaggio dell'evento
            data (Optional[Dict[str, Any]]): Dati aggiuntivi
            error (Optional[Exception]): Eccezione associata
        """
        logger = self.get_logger(component)

        # Prepara i dati strutturati
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'level': level,
            'message': message,
            'data': data or {}
        }

        if error:
            import traceback
            log_data['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }

        # Logga in base al livello
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(json.dumps(log_data, indent=2, default=str))

    def log_performance(self, component: str, operation: str,
                        duration: float, success: bool = True,
                        details: Optional[Dict[str, Any]] = None):
        """
        Logga informazioni sulle performance.

        Args:
            component (str): Componente che ha eseguito l'operazione
            operation (str): Nome dell'operazione
            duration (float): Durata in secondi
            success (bool): Se l'operazione è riuscita
            details (Optional[Dict[str, Any]]): Dettagli aggiuntivi
        """
        data = {
            'operation': operation,
            'duration': duration,
            'success': success,
            'performance_ms': duration * 1000
        }

        if details:
            data.update(details)

        level = 'INFO' if success else 'WARNING'
        self.log_event(component, level, "Performance: {operation}", data)

    def log_user_action(self, action: str, user_id: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None):
        """
        Logga un'azione dell'utente.

        Args:
            action (str): Azione eseguita dall'utente
            user_id (Optional[str]): ID dell'utente
            details (Optional[Dict[str, Any]]): Dettagli aggiuntivi
        """
        data = {'action': action}
        if user_id:
            data['user_id'] = user_id
        if details:
            data.update(details)

        self.log_event('USER', 'INFO', "User action: {action}", data)

    def log_system_event(self, event_type: str, message: str,
                         details: Optional[Dict[str, Any]] = None):
        """
        Logga un evento di sistema.

        Args:
            event_type (str): Tipo di evento (STARTUP, SHUTDOWN, ERROR, etc.)
            message (str): Messaggio dell'evento
            details (Optional[Dict[str, Any]]): Dettagli aggiuntivi
        """
        data = {'event_type': event_type}
        if details:
            data.update(details)

        self.log_event('SYSTEM', 'INFO', "System event: {event_type} - {message}", data)

    def log_ai_interaction(self, model: str, prompt: str, response: str,
                           duration: float, success: bool = True):
        """
        Logga un'interazione con l'AI.

        Args:
            model (str): Modello AI utilizzato
            prompt (str): Prompt inviato
            response (str): Risposta ricevuta
            duration (float): Durata della richiesta
            success (bool): Se la richiesta è riuscita
        """
        data = {
            'model': model,
            'prompt_length': len(prompt),
            'response_length': len(response),
            'duration': duration,
            'success': success
        }

        level = 'INFO' if success else 'ERROR'
        self.log_event('AI', level, "AI interaction with {model}", data)

    def log_video_processing(self, operation: str, frame_count: int,
                             processing_time: float, success: bool = True,
                             details: Optional[Dict[str, Any]] = None):
        """
        Logga operazioni di processamento video.

        Args:
            operation (str): Tipo di operazione (detection, tracking, etc.)
            frame_count (int): Numero di frame processati
            processing_time (float): Tempo di processamento
            success (bool): Se l'operazione è riuscita
            details (Optional[Dict[str, Any]]): Dettagli aggiuntivi
        """
        data = {
            'operation': operation,
            'frame_count': frame_count,
            'processing_time': processing_time,
            'fps': frame_count / processing_time if processing_time > 0 else 0,
            'success': success
        }

        if details:
            data.update(details)

        level = 'DEBUG' if success else 'WARNING'
        self.log_event('VIDEO', level, "Video processing: {operation}", data)

    def log_audio_event(self, event_type: str, duration: Optional[float] = None,
                        text: Optional[str] = None, success: bool = True):
        """
        Logga eventi audio.

        Args:
            event_type (str): Tipo di evento (TTS, STT, PLAYBACK, etc.)
            duration (Optional[float]): Durata dell'evento
            text (Optional[str]): Testo associato
            success (bool): Se l'evento è riuscito
        """
        data = {'event_type': event_type, 'success': success}

        if duration is not None:
            data['duration'] = duration
        if text:
            data['text_length'] = len(text)

        level = 'INFO' if success else 'ERROR'
        self.log_event('AUDIO', level, "Audio event: {event_type}", data)

    def create_session_log(self, session_id: str) -> logging.Logger:
        """
        Crea un logger specifico per una sessione.

        Args:
            session_id (str): ID della sessione

        Returns:
            logging.Logger: Logger per la sessione
        """
        session_logger = logging.getLogger("{self.app_name}.SESSION.{session_id}")

        # Handler specifico per la sessione
        session_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, "session_{session_id}.log"),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=2
        )
        session_formatter = logging.Formatter(
            '%(asctime)s - SESSION:%(name)s - %(levelname)s - %(message)s'
        )
        session_handler.setFormatter(session_formatter)
        session_handler.setLevel(logging.DEBUG)
        session_logger.addHandler(session_handler)

        return session_logger

    def cleanup_old_logs(self, days: int = 30):
        """
        Pulisce i file di log più vecchi di un certo numero di giorni.

        Args:
            days (int): Numero di giorni dopo cui eliminare i log
        """
        import time
        import glob

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        # Trova tutti i file di log
        log_files = glob.glob(os.path.join(self.log_dir, "*.log*"))

        for log_file in log_files:
            if os.path.getmtime(log_file) < cutoff_time:
                try:
                    os.remove(log_file)
                    self.root_logger.info("Log file cleaned up: {log_file}")
                except OSError as e:
                    self.root_logger.error("Error cleaning up log file {log_file}: {e}")


# Istanza globale del logger
global_logger = StructuredLogger()


def get_component_logger(component: str) -> logging.Logger:
    """
    Funzione di utilità per ottenere un logger per componente.

    Args:
        component (str): Nome del componente

    Returns:
        logging.Logger: Logger per il componente
    """
    return global_logger.get_logger(component)


def log_performance(component: str, operation: str, duration: float,
                    success: bool = True, details: Optional[Dict[str, Any]] = None):
    """
    Funzione di utilità per loggare performance.

    Args:
        component (str): Componente
        operation (str): Operazione
        duration (float): Durata
        success (bool): Successo
        details (Optional[Dict[str, Any]]): Dettagli
    """
    global_logger.log_performance(component, operation, duration, success, details)


def log_error(component: str, message: str, error: Optional[Exception] = None,
              data: Optional[Dict[str, Any]] = None):
    """
    Funzione di utilità per loggare errori.

    Args:
        component (str): Componente
        message (str): Messaggio
        error (Optional[Exception]): Eccezione
        data (Optional[Dict[str, Any]]): Dati aggiuntivi
    """
    global_logger.log_event(component, 'ERROR', message, data, error)
