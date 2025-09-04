# cpu_handlers.py - Gestori per le funzioni CPU e monitoraggio

import logging
from PyQt6.QtWidgets import QMessageBox

from CPU_Check_Temperature.cpu_monitor import CPUMonitor


class CPUHandlers:
    """Classe che gestisce tutte le funzioni CPU e monitoraggio."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)

    def initialize_cpu_monitor(self):
        """Inizializza il monitoraggio della CPU."""
        try:
            self.main_window.cpu_monitor = CPUMonitor(self.main_window.settings, self.main_window)

            # Connetti i segnali
            self.main_window.cpu_monitor.cpu_warning.connect(self.on_cpu_warning)
            self.main_window.cpu_monitor.cpu_critical.connect(self.on_cpu_critical)
            self.main_window.cpu_monitor.temperature_warning.connect(self.on_temperature_warning)
            self.main_window.cpu_monitor.temperature_critical.connect(self.on_temperature_critical)

            # Avvia il monitoraggio
            self.main_window.cpu_monitor.start()

            logging.info("Monitoraggio CPU inizializzato")

        except Exception as e:
            logging.error(f"Errore nell'inizializzazione del monitoraggio CPU: {e}")
            self.main_window.cpu_monitor = None

    def on_cpu_warning(self, message):
        """Gestisce gli avvisi di CPU alta."""
        logging.warning(f"Avviso CPU: {message}")

        # Mostra un messaggio all'utente
        QMessageBox.warning(self.main_window, "Avviso CPU Alta",
                           f"L'applicazione sta utilizzando molta CPU:\n\n{message}\n\n"
                           "Considera di chiudere alcune applicazioni o riavviare il sistema.")

    def on_cpu_critical(self, message):
        """Gestisce situazioni critiche di CPU."""
        logging.critical(f"CPU Critica: {message}")

        # Mostra un messaggio critico all'utente
        QMessageBox.critical(self.main_window, "CPU Critica - Terminazione",
                            f"L'applicazione ha superato i limiti di CPU consentiti:\n\n{message}\n\n"
                            "L'applicazione verrà terminata per proteggere il sistema.")

    def on_temperature_warning(self, message):
        """Gestisce gli avvisi di temperatura alta."""
        logging.warning(f"Avviso Temperatura: {message}")

        # Mostra un messaggio di avviso all'utente
        QMessageBox.warning(self.main_window, "Avviso Temperatura Alta",
                           f"La temperatura del processore è elevata:\n\n{message}\n\n"
                           "Considera di:\n"
                           "• Chiudere altre applicazioni\n"
                           "• Migliorare la ventilazione\n"
                           "• Controllare le ventole del sistema")

    def on_temperature_critical(self, message):
        """Gestisce situazioni critiche di temperatura."""
        logging.critical(f"Temperatura Critica: {message}")

        # Mostra un messaggio critico all'utente
        QMessageBox.critical(self.main_window, "Temperatura Critica - Terminazione",
                            f"La temperatura del processore è CRITICAMENTE alta:\n\n{message}\n\n"
                            "L'applicazione verrà terminata per proteggere l'hardware.")