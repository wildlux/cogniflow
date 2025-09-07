# voice_handlers.py - Gestori per le funzioni TTS e riconoscimento vocale

import logging
from PyQt6.QtWidgets import QMessageBox

from ...Riconoscimento_Vocale.managers.speech_recognition_manager import SpeechRecognitionThread


class VoiceHandlers:
    """Classe che gestisce tutte le funzioni TTS e riconoscimento vocale."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

    def handle_voice_button(self):
        """Avvia il riconoscimento vocale quando si clicca il pulsante voce."""
        self.main_window.btn_voice.setEnabled(False)
        self.main_window.btn_voice.setText("🎤 In registrazione...")

        # Utilizza il modello Vosk selezionato invece del lang_code
        vosk_model = self.main_window.settings.get('vosk_model', 'vosk-model-it-0.22')

        # Se il modello non è configurato, selezionalo automaticamente in base alla lingua
        if not vosk_model or vosk_model == 'auto':
            lang_code = self.main_window.settings.get('language', 'it-IT')
            vosk_model = self.get_vosk_model_for_language(lang_code)
            # Salva la selezione automatica
            self.main_window.settings['vosk_model'] = vosk_model
            import json
            with open("Save/SETUP_TOOLS_&_Data/settings.json", "w", encoding='utf-8') as f:
                json.dump(self.main_window.settings, f, indent=4, ensure_ascii=False)

        # Verifica che il modello esista
        model_path = os.path.join("Audio", "vosk_models", vosk_model)
        if not os.path.exists(model_path):
            QMessageBox.warning(self.main_window, "Modello Vosk Mancante",
                                "Il modello Vosk '{vosk_model}' non è stato trovato.\n\n"
                                "Percorso cercato: {model_path}\n\n"
                                "Assicurati di aver scaricato il modello dalla sezione 'Controllo Librerie'.\n\n"
                                "Modelli disponibili:\n"
                                "• vosk-model-it-0.22 (Italiano completo)\n"
                                "• vosk-model-small-it-0.22 (Italiano piccolo)\n"
                                "• vosk-model-small-en-us-0.15 (Inglese)")
            self.main_window.btn_voice.setEnabled(True)
            self.main_window.btn_voice.setText("🎤 Trascrivi")
            return

        self.main_window.speech_rec_thread = SpeechRecognitionThread(vosk_model)
        self.main_window.speech_rec_thread.recognized_text.connect(self.on_voice_recognized)
        self.main_window.speech_rec_thread.recognition_error.connect(self.on_voice_error)
        self.main_window.speech_rec_thread.finished.connect(lambda: self.main_window.btn_voice.setEnabled(True))
        self.main_window.speech_rec_thread.start()

        logging.info("Riconoscimento vocale avviato con modello: {vosk_model}")

    def on_voice_recognized(self, text):
        """Riceve il testo riconosciuto e lo inserisce nell'area di dettaglio."""
        self.main_window.work_area_left_text_edit.append(text)
        self.main_window.btn_voice.setText("🎤 Trascrivi")

    def on_voice_error(self, message):
        """Mostra un messaggio di errore in caso di fallimento del riconoscimento vocale."""
        QMessageBox.warning(self.main_window, "Riconoscimento Vocale", message)
        self.main_window.btn_voice.setText("🎤 Trascrivi")

    def get_vosk_model_for_language(self, language_code):
        """
        Restituisce il modello Vosk appropriato per la lingua selezionata.
        """
        model_mapping = {
            'it-IT': 'vosk-model-it-0.22',
            'it': 'vosk-model-it-0.22',
            'en-US': 'vosk-model-small-en-us-0.15',
            'en': 'vosk-model-small-en-us-0.15',
            'es-ES': 'vosk-model-small-en-us-0.15',  # Fallback to English
            'fr-FR': 'vosk-model-small-en-us-0.15',  # Fallback to English
            'de-DE': 'vosk-model-small-en-us-0.15'   # Fallback to English
        }

        return model_mapping.get(language_code, 'vosk-model-it-0.22')

    def check_vosk_models_availability(self):
        """
        Verifica quali modelli Vosk sono disponibili e restituisce una lista.
        """
        available_models = []
        vosk_models_dir = os.path.join("Audio", "vosk_models")

        if os.path.exists(vosk_models_dir):
            for item in os.listdir(vosk_models_dir):
                item_path = os.path.join(vosk_models_dir, item)
                if os.path.isdir(item_path):
                    available_models.append(item)

        return available_models
