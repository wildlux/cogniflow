#!/usr/bin/env python3
"""
User-Friendly Error Messages - CogniFLow
Sistema per convertire errori tecnici in messaggi comprensibili per l'utente
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class UserFriendlyErrorHandler:
    """Gestore di errori user-friendly per l'applicazione CogniFLow."""

    def __init__(self):
        # Mappa degli errori tecnici a messaggi user-friendly
        self.error_mappings = {
            # Errori AI
            "Connection refused": {
                "title": "🤖 Servizio AI Non Raggiungibile",
                "message": "Il servizio di intelligenza artificiale non è attualmente disponibile.\n\n"
                "💡 Possibili soluzioni:\n"
                "• Verifica che Ollama sia installato e in esecuzione\n"
                "• Controlla la connessione internet\n"
                "• Riprova tra qualche minuto\n\n"
                "🔧 Comando per avviare: ollama serve",
                "icon": QMessageBox.Icon.Warning,
            },
            "timeout": {
                "title": "⏰ Richiesta Scaduta",
                "message": "La richiesta al servizio AI ha impiegato troppo tempo.\n\n"
                "💡 Possibili cause:\n"
                "• Connessione internet lenta\n"
                "• Il modello AI è sovraccarico\n"
                "• Testo troppo lungo da elaborare\n\n"
                "🔄 Riprova con un testo più breve o più tardi.",
                "icon": QMessageBox.Icon.Warning,
            },
            "model not found": {
                "title": "🧠 Modello AI Non Trovato",
                "message": "Il modello di intelligenza artificiale richiesto non è disponibile.\n\n"
                "💡 Soluzioni:\n"
                "• Scarica il modello richiesto\n"
                "• Usa un modello diverso dalle impostazioni\n"
                "• Verifica lo spazio disponibile su disco\n\n"
                "📋 Modelli disponibili: llama2:7b, gemma:2b",
                "icon": QMessageBox.Icon.Information,
            },
            # Errori riconoscimento vocale
            "No module named 'vosk'": {
                "title": "🎤 Libreria Riconoscimento Vocale Mancante",
                "message": "La libreria per il riconoscimento vocale non è installata.\n\n"
                "💡 Per installare:\n"
                "• Apri il terminale\n"
                "• Digita: pip install vosk pyaudio\n"
                "• Riavvia l'applicazione\n\n"
                "🎵 Il riconoscimento vocale sarà disponibile dopo l'installazione.",
                "icon": QMessageBox.Icon.Information,
            },
            "Audio device": {
                "title": "🎙️ Microfono Non Rilevato",
                "message": "Non è stato possibile accedere al microfono.\n\n"
                "💡 Verifica:\n"
                "• Che il microfono sia collegato\n"
                "• Che non sia utilizzato da altre applicazioni\n"
                "• Le impostazioni privacy del microfono\n"
                "• Che il microfono sia selezionato come dispositivo predefinito\n\n"
                "🔧 Controlla nelle impostazioni audio del sistema.",
                "icon": QMessageBox.Icon.Warning,
            },
            # Errori OCR
            "No module named 'pytesseract'": {
                "title": "📄 Libreria OCR Mancante",
                "message": "La libreria per il riconoscimento ottico dei caratteri non è installata.\n\n"
                "💡 Per installare:\n"
                "• pip install pytesseract pillow\n"
                "• Scarica Tesseract-OCR dal sito ufficiale\n"
                "• Aggiungi Tesseract al PATH di sistema\n\n"
                "📖 L'OCR sarà disponibile dopo l'installazione.",
                "icon": QMessageBox.Icon.Information,
            },
            "tesseract": {
                "title": "⚙️ Tesseract Non Configurato",
                "message": "Il motore OCR Tesseract non è configurato correttamente.\n\n"
                "💡 Verifica:\n"
                "• Che Tesseract sia installato\n"
                "• Che sia nel PATH di sistema\n"
                "• La versione di Tesseract (consigliata 4.1+)\n\n"
                "🔧 Scarica da: https://github.com/UB-Mannheim/tesseract/wiki",
                "icon": QMessageBox.Icon.Warning,
            },
            # Errori file system
            "Permission denied": {
                "title": "🔒 Permesso Negato",
                "message": "Non hai i permessi necessari per accedere al file o cartella.\n\n"
                "💡 Soluzioni:\n"
                "• Esegui l'applicazione come amministratore\n"
                "• Verifica i permessi del file/cartella\n"
                "• Scegli una posizione diversa per salvare\n"
                "• Controlla le impostazioni antivirus\n\n"
                "📂 Prova a salvare in Documenti o Desktop.",
                "icon": QMessageBox.Icon.Warning,
            },
            "No space left": {
                "title": "💾 Spazio Disco Esaurito",
                "message": "Non c'è spazio sufficiente sul disco per completare l'operazione.\n\n"
                "💡 Azioni consigliate:\n"
                "• Libera spazio sul disco\n"
                "• Elimina file temporanei non necessari\n"
                "• Sposta file su un altro disco\n"
                "• Chiudi altre applicazioni\n\n"
                "🗂️ Controlla lo spazio disponibile nelle proprietà del disco.",
                "icon": QMessageBox.Icon.Warning,
            },
            "File not found": {
                "title": "📄 File Non Trovato",
                "message": "Il file che stai cercando non è stato trovato.\n\n"
                "💡 Possibili cause:\n"
                "• Il file è stato spostato o eliminato\n"
                "• Percorso non corretto\n"
                "• File corrotto o danneggiato\n\n"
                "🔍 Verifica il percorso e riprova.",
                "icon": QMessageBox.Icon.Warning,
            },
            # Errori di rete
            "Network is unreachable": {
                "title": "🌐 Rete Non Raggiungibile",
                "message": "Impossibile connettersi alla rete.\n\n"
                "💡 Verifica:\n"
                "• Connessione internet attiva\n"
                "• Firewall e antivirus\n"
                "• Impostazioni proxy\n"
                "• Connessione Wi-Fi o Ethernet\n\n"
                "🔄 Riprova dopo aver verificato la connessione.",
                "icon": QMessageBox.Icon.Warning,
            },
            "Connection timed out": {
                "title": "⏱️ Connessione Scaduta",
                "message": "La connessione ha impiegato troppo tempo per rispondere.\n\n"
                "💡 Possibili soluzioni:\n"
                "• Verifica la velocità della connessione\n"
                "• Riprova più tardi\n"
                "• Controlla se il servizio è temporaneamente non disponibile\n"
                "• Usa una connessione diversa\n\n"
                "🔄 L'operazione verrà ritentata automaticamente.",
                "icon": QMessageBox.Icon.Warning,
            },
            # Errori generici
            "MemoryError": {
                "title": "🧠 Memoria Insufficiente",
                "message": "La memoria del sistema non è sufficiente per completare l'operazione.\n\n"
                "💡 Suggerimenti:\n"
                "• Chiudi altre applicazioni\n"
                "• Riavvia il computer\n"
                "• Aumenta la RAM se possibile\n"
                "• Riduci la dimensione dei file elaborati\n\n"
                "💾 Libera memoria chiudendo programmi non necessari.",
                "icon": QMessageBox.Icon.Warning,
            },
            "KeyboardInterrupt": {
                "title": "⏹️ Operazione Interrotta",
                "message": "L'operazione è stata interrotta dall'utente.\n\n"
                "Non è stato completato nulla di dannoso.\n"
                "Puoi riavviare l'operazione quando vuoi.",
                "icon": QMessageBox.Icon.Information,
            },
        }

        # Errori di import comuni
        self.import_error_mappings = {
            "Artificial_Intelligence": "🤖 Moduli AI",
            "UI": "🖥️ Interfaccia Utente",
            "core": "⚙️ Componenti Core",
            "PyQt6": "🖼️ Libreria Grafica Qt6",
            "vosk": "🎤 Riconoscimento Vocale",
            "pytesseract": "📄 OCR",
            "PIL": "🖼️ Elaborazione Immagini",
            "psutil": "📊 Monitor Sistema",
        }

    def get_user_friendly_error(
        self, error: Exception, context: str = ""
    ) -> Dict[str, Any]:
        """
        Converte un errore tecnico in un messaggio user-friendly.

        Args:
            error: L'eccezione originale
            context: Contesto aggiuntivo per il messaggio

        Returns:
            Dict con title, message, e icon per QMessageBox
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Cerca corrispondenze specifiche
        for key, mapping in self.error_mappings.items():
            if key.lower() in error_str or key.lower() in error_type.lower():
                return mapping

        # Gestisci errori di import specifici
        if "No module named" in str(error):
            return self._handle_import_error(error)

        # Errore generico
        return {
            "title": "⚠️ Errore Inaspettato",
            "message": f"Si è verificato un errore imprevisto.\n\n"
            f"📋 Dettagli tecnici: {str(error)}\n\n"
            f"💡 Suggerimenti:\n"
            f"• Riavvia l'applicazione\n"
            f"• Verifica la connessione internet\n"
            f"• Contatta il supporto se il problema persiste\n\n"
            f"📝 Il team di sviluppo è stato informato.",
            "icon": QMessageBox.Icon.Warning,
        }

    def _handle_import_error(self, error: Exception) -> Dict[str, Any]:
        """Gestisce errori di import specifici."""
        error_str = str(error)

        # Estrai il nome del modulo dall'errore
        if "No module named '" in error_str:
            module_name = error_str.split("No module named '")[1].split("'")[0]

            # Cerca una corrispondenza user-friendly
            friendly_name = self.import_error_mappings.get(module_name, module_name)

            return {
                "title": f"📦 Libreria Mancante: {friendly_name}",
                "message": f"La libreria '{friendly_name}' non è installata.\n\n"
                f"💡 Per installare:\n"
                f"• Apri il terminale o prompt dei comandi\n"
                f"• Digita: pip install {module_name}\n"
                f"• Premi Invio e attendi il completamento\n"
                f"• Riavvia l'applicazione\n\n"
                f"🔧 Se hai problemi, consulta la documentazione.",
                "icon": QMessageBox.Icon.Information,
            }

        return self.error_mappings.get(
            "generic",
            {
                "title": "📦 Libreria Mancante",
                "message": f"Una libreria necessaria non è installata.\n\n"
                f"💡 Prova a installare le dipendenze con:\n"
                f"pip install -r requirements.txt\n\n"
                f"📋 Errore originale: {str(error)}",
                "icon": QMessageBox.Icon.Warning,
            },
        )

    def show_error_dialog(self, parent, error: Exception, context: str = ""):
        """
        Mostra un dialog di errore user-friendly.

        Args:
            parent: Widget parent per il dialog
            error: L'eccezione da mostrare
            context: Contesto aggiuntivo
        """
        friendly_error = self.get_user_friendly_error(error, context)

        # Log dell'errore originale per debug
        logger.error("User-friendly error shown: {error}")

        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(friendly_error["title"])
        msg_box.setText(friendly_error["message"])
        msg_box.setIcon(friendly_error["icon"])
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Aggiungi pulsante "Dettagli tecnici" se disponibile
        if hasattr(error, "__traceback__"):
            msg_box.setDetailedText(f"Errore tecnico completo:\n{str(error)}")

        msg_box.exec()

    def get_success_message(self, operation: str, details: str = "") -> Dict[str, Any]:
        """
        Restituisce un messaggio di successo user-friendly.

        Args:
            operation: Tipo di operazione completata
            details: Dettagli aggiuntivi

        Returns:
            Dict con title e message
        """
        success_messages = {
            "ai_response": {
                "title": "🎉 Risposta AI Ricevuta!",
                "message": f"Eccellente! L'intelligenza artificiale ha elaborato la tua richiesta.\n\n{details}",
            },
            "voice_recognition": {
                "title": "🎤 Testo Riconosciuto!",
                "message": f"Perfetto! Il tuo discorso è stato trascritto correttamente.\n\n{details}",
            },
            "ocr_complete": {
                "title": "📄 OCR Completato!",
                "message": "Ottimo! Il testo è stato estratto dall'immagine.\n\n{details}",
            },
            "file_saved": {
                "title": "💾 File Salvato!",
                "message": "Il tuo lavoro è stato salvato correttamente.\n\n{details}",
            },
            "file_loaded": {
                "title": "📂 File Caricato!",
                "message": "Il progetto è stato caricato con successo.\n\n{details}",
            },
        }

        return success_messages.get(
            operation,
            {
                "title": "✅ Operazione Completata!",
                "message": "L'operazione è stata completata con successo.\n\n{details}",
            },
        )


# Istanza globale dell'error handler
error_handler = UserFriendlyErrorHandler()


def show_user_friendly_error(parent, error: Exception, context: str = ""):
    """Funzione di comodo per mostrare errori user-friendly."""
    error_handler.show_error_dialog(parent, error, context)


def get_user_friendly_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Funzione di comodo per ottenere messaggi di errore user-friendly."""
    return error_handler.get_user_friendly_error(error, context)


def show_success_message(parent, operation: str, details: str = ""):
    """Funzione di comodo per mostrare messaggi di successo."""
    success_info = error_handler.get_success_message(operation, details)

    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(success_info["title"])
    msg_box.setText(success_info["message"])
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()
