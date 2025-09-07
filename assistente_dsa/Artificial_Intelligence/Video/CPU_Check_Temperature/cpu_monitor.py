# cpu_monitor.py - Monitoraggio CPU e temperatura

import time
import signal
import logging
import os
from PyQt6.QtCore import QThread, pyqtSignal

# Import per monitoraggio CPU e temperatura
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


class CPUMonitor(QThread):
    """Thread per il monitoraggio dell'utilizzo della CPU e temperatura."""

    cpu_warning = pyqtSignal(str)  # Segnale per avvisi CPU alta
    cpu_critical = pyqtSignal(str)  # Segnale per CPU critica
    temperature_warning = pyqtSignal(str)  # Segnale per avvisi temperatura alta
    temperature_critical = pyqtSignal(str)  # Segnale per temperatura critica

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.is_running = True
        self.high_cpu_start_time = None
        self.high_temp_start_time = None
        self.process = None

        # Ottieni il PID del processo corrente
        try:
            if HAS_PSUTIL:
                self.process = psutil.Process(os.getpid())
            else:
                self.process = None
        except Exception:
            logging.warning("Impossibile ottenere il processo per monitoraggio CPU: {e}")
            self.process = None

    def run(self):
        """Loop principale del monitoraggio CPU e temperatura."""
        while self.is_running:
            try:
                current_time = time.time()
                check_interval = self.settings.get('cpu_check_interval_seconds', 5)

                # Monitoraggio CPU
                if self.settings.get('cpu_monitoring_enabled', True):
                    cpu_percent = self.get_cpu_usage()
                    cpu_threshold = self.settings.get('cpu_threshold_percent', 95.0)
                    cpu_high_duration = self.settings.get('cpu_high_duration_seconds', 30)

                    if cpu_percent >= cpu_threshold:
                        if self.high_cpu_start_time is None:
                            self.high_cpu_start_time = current_time
                            logging.info(".1f")
                        else:
                            duration = current_time - self.high_cpu_start_time
                            if duration >= cpu_high_duration:
                                self.handle_high_cpu_duration(cpu_percent, duration)
                    else:
                        if self.high_cpu_start_time is not None:
                            duration = current_time - self.high_cpu_start_time
                            logging.info(".1f")
                            self.high_cpu_start_time = None

                # Monitoraggio temperatura
                if self.settings.get('temperature_monitoring_enabled', True):
                    temperature = self.get_temperature()
                    if temperature is not None:
                        temp_threshold = self.settings.get('temperature_threshold_celsius', 80.0)
                        temp_high_duration = self.settings.get('temperature_high_duration_seconds', 60)
                        temp_critical = self.settings.get('temperature_critical_threshold', 90.0)

                        if temperature >= temp_critical:
                            self.handle_critical_temperature(temperature)
                        elif temperature >= temp_threshold:
                            if self.high_temp_start_time is None:
                                self.high_temp_start_time = current_time
                                logging.info(".1f")
                            else:
                                duration = current_time - self.high_temp_start_time
                                if duration >= temp_high_duration:
                                    self.handle_high_temperature_duration(temperature, duration)
                        else:
                            if self.high_temp_start_time is not None:
                                duration = current_time - self.high_temp_start_time
                                logging.info(".1f")
                                self.high_temp_start_time = None

                time.sleep(check_interval)

            except Exception:
                logging.error("Errore nel monitoraggio CPU/temperatura: {e}")
                time.sleep(5)  # Pausa più lunga in caso di errore

    def get_cpu_usage(self):
        """Ottiene l'utilizzo della CPU del processo corrente."""
        try:
            if HAS_PSUTIL and self.process:
                # Utilizzo CPU del processo specifico
                return self.process.cpu_percent(interval=1)
            else:
                # Fallback: utilizzo CPU totale del sistema
                if HAS_PSUTIL:
                    import psutil
                    return psutil.cpu_percent(interval=1)
                else:
                    return 0.0
        except Exception:
            logging.error("Errore nella lettura CPU: {e}")
            return 0.0

    def get_temperature(self):
        """Ottiene la temperatura del processore."""
        try:
            if HAS_PSUTIL:
                # Prova a ottenere la temperatura usando psutil
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Cerca temperature della CPU
                        for name, entries in temps.items():
                            if 'cpu' in name.lower() or 'core' in name.lower():
                                if entries:
                                    # Prendi la temperatura più alta
                                    return max(entry.current for entry in entries if hasattr(entry, 'current'))

            # Fallback per Linux: lettura diretta da /sys/class/thermal/
            if os.name == 'posix' and os.path.exists('/sys/class/thermal/'):
                try:
                    thermal_zones = [d for d in os.listdir('/sys/class/thermal/') if d.startswith('thermal_zone')]
                    for zone in thermal_zones:
                        temp_file = f'/sys/class/thermal/{zone}/temp'
                        if os.path.exists(temp_file):
                            with open(temp_file, 'r') as f:
                                temp_millidegree = int(f.read().strip())
                                temp_celsius = temp_millidegree / 1000.0
                                if temp_celsius > 0:  # Valore valido
                                    return temp_celsius
                except Exception:
                    logging.debug("Errore lettura temperatura Linux: {e}")

            # Fallback per Windows usando wmi (se disponibile)
            if HAS_WMI:
                try:
                    w = wmi.WMI(namespace="root\\wmi")
                    temperature_info = w.MSAcpi_ThermalZoneTemperature()
                    for temp in temperature_info:
                        if hasattr(temp, 'CurrentTemperature'):
                            temp_celsius = (temp.CurrentTemperature - 2732) / 10.0  # Convert from tenths of Kelvin
                            if temp_celsius > 0:
                                return temp_celsius
                except Exception:
                    logging.debug("Errore lettura temperatura Windows: {e}")

            return None

        except Exception:
            logging.error("Errore nella lettura della temperatura: {e}")
            return None

    def handle_high_cpu_duration(self, cpu_percent, duration):
        """Gestisce il caso di CPU alta per troppo tempo."""
        try:
            signal_type = self.settings.get('cpu_signal_type', 'SIGTERM')
            message = ".1f"

            logging.critical(message)
            self.cpu_critical.emit(message)

            # Invia il segnale appropriato
            self.send_cpu_signal(signal_type)

        except Exception:
            logging.error("Errore nella gestione CPU alta: {e}")

    def handle_critical_temperature(self, temperature):
        """Gestisce temperature critiche che richiedono azione immediata."""
        try:
            signal_type = self.settings.get('cpu_signal_type', 'SIGTERM')
            message = ".1f"

            logging.critical(message)
            self.temperature_critical.emit(message)

            # Invia segnale immediato per temperature critiche
            self.send_cpu_signal(signal_type)

        except Exception:
            logging.error("Errore nella gestione temperatura critica: {e}")

    def handle_high_temperature_duration(self, temperature, duration):
        """Gestisce temperature alte per troppo tempo."""
        try:
            message = ".1f"

            logging.warning(message)
            self.temperature_warning.emit(message)

        except Exception:
            logging.error("Errore nella gestione temperatura elevata: {e}")

    def send_cpu_signal(self, signal_type):
        """Invia un segnale al sistema operativo per alto utilizzo CPU."""
        try:
            current_pid = os.getpid()

            if signal_type == 'SIGTERM':
                sig = signal.SIGTERM
                sig_name = 'SIGTERM'
            elif signal_type == 'SIGKILL':
                sig = signal.SIGKILL
                sig_name = 'SIGKILL'
            elif signal_type == 'SIGUSR1':
                sig = signal.SIGUSR1
                sig_name = 'SIGUSR1'
            else:
                logging.error("Tipo di segnale non supportato: {signal_type}")
                return

            logging.critical(f"Invio segnale {sig_name} (PID: {current_pid}) per alto utilizzo CPU")

            # Invia il segnale al processo corrente
            os.kill(current_pid, sig)

        except Exception:
            logging.error("Errore nell'invio del segnale CPU: {e}")

    def stop(self):
        """Ferma il monitoraggio CPU."""
        self.is_running = False
        self.wait()
