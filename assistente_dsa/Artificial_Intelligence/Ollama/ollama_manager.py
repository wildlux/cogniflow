# AI/Ollama/ollama_manager.py
# Gestione centralizzata di Ollama e dei suoi modelli

import json
import logging
import os
import subprocess
import requests
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal


class OllamaManager:
    """Gestore centralizzato per Ollama e i suoi modelli."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.models_dir = os.path.join(os.path.dirname(__file__), "models")
        self.configs_dir = os.path.join(os.path.dirname(__file__), "configs")
        self.logs_dir = os.path.join(os.path.dirname(__file__), "logs")

        # Assicurati che le directory esistano
        for directory in [self.models_dir, self.configs_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)

        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configura il logging per Ollama."""
        logger = logging.getLogger("OllamaManager")
        logger.setLevel(logging.INFO)

        log_file = os.path.join(self.logs_dir, "ollama_manager.log")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    def check_ollama_running(self) -> bool:
        """Verifica se Ollama è in esecuzione."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama non è raggiungibile: {e}")
            return False

    def start_ollama_service(self) -> bool:
        """Avvia il servizio Ollama se non è già in esecuzione."""
        try:
            # Controlla se è già in esecuzione
            if self.check_ollama_running():
                self.logger.info("Ollama è già in esecuzione")
                return True

            # Avvia Ollama
            self.logger.info("Avvio del servizio Ollama...")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Attendi che si avvii
            for i in range(30):  # 30 secondi di timeout
                if self.check_ollama_running():
                    self.logger.info("Ollama avviato con successo")
                    return True
                time.sleep(1)

            self.logger.error("Timeout nell'avvio di Ollama")
            return False

        except Exception:
            self.logger.error("Errore nell'avvio di Ollama: {e}")
            return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Ottiene la lista dei modelli disponibili localmente."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            self.logger.error(f"Errore nel recupero dei modelli: {e}")
            return []

    def list_models(self) -> List[Dict[str, Any]]:
        """Alias per get_available_models per compatibilità."""
        return self.get_available_models()

    def pull_model(self, model_name: str) -> bool:
        """Scarica un modello specifico."""
        try:
            self.logger.info(f"Scaricamento del modello: {model_name}")

            # Usa subprocess per evitare blocchi
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minuti di timeout
            )

            if result.returncode == 0:
                self.logger.info(f"Modello {model_name} scaricato con successo")
                return True
            else:
                self.logger.error(
                    f"Errore nel download di {model_name}: {result.stderr}"
                )
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout nel download di {model_name}")
            return False
        except Exception as e:
            self.logger.error(f"Errore nel download di {model_name}: {e}")
            return False

    def install_recommended_models(self) -> Dict[str, bool]:
        """Installa i modelli raccomandati per l'assistente DSA."""
        recommended_models = {
            "llava:7b": "Modello vision-language per riconoscimento immagini",
            "llama2:7b": "Modello di linguaggio generale",
            "codellama:7b": "Modello specializzato in codice",
            "mistral:7b": "Modello efficiente e performante",
            "phi:3b": "Modello leggero e veloce",
        }

        results = {}

        for model_name, description in recommended_models.items():
            self.logger.info(f"Installazione {model_name}: {description}")
            success = self.pull_model(model_name)
            results[model_name] = success

            if success:
                self.logger.info(f"✅ {model_name} installato con successo")
            else:
                self.logger.error(f"❌ Errore nell'installazione di {model_name}")

        return results

    def generate_text(
        self,
        prompt: str,
        model: str = "gemma:2b",
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Genera testo usando un modello specifico."""
        try:
            payload = {"model": model, "prompt": prompt, "stream": False}

            if options:
                payload["options"] = options

            response = requests.post(
                f"{self.base_url}/api/generate", json=payload, timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                self.logger.error(f"Errore nella generazione: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Errore nella generazione di testo: {e}")
            return None

    def save_model_config(self, model_name: str, config: Dict[str, Any]) -> bool:
        """Salva la configurazione di un modello."""
        try:
            config_file = os.path.join(
                self.configs_dir, f"{model_name.replace(':', '_')}.json"
            )

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configurazione salvata per {model_name}")
            return True

        except Exception as e:
            self.logger.error(f"Errore nel salvataggio della configurazione: {e}")
            return False

    def load_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Carica la configurazione di un modello."""
        try:
            config_file = os.path.join(
                self.configs_dir, f"{model_name.replace(':', '_')}.json"
            )

            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None

        except Exception as e:
            self.logger.error(f"Errore nel caricamento della configurazione: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sul sistema Ollama."""
        info = {
            "running": self.check_ollama_running(),
            "models": [],
            "version": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Versione
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code == 200:
                info["version"] = response.json().get("version")

            # Modelli
            info["models"] = self.get_available_models()

        except Exception as e:
            self.logger.error(f"Errore nel recupero delle informazioni di sistema: {e}")

        return info


# Istanza globale per uso facile
ollama_manager = OllamaManager()

# Funzioni di utilità per retrocompatibilità


def check_ollama_connection():
    """Funzione di compatibilità per controllare la connessione."""
    return ollama_manager.check_ollama_running()


def get_ollama_models():
    """Funzione di compatibilità per ottenere i modelli."""
    return ollama_manager.get_available_models()


# ==============================================================================
# Classi Thread per PyQt6 (aggiunte per compatibilità)
# ==============================================================================


class OllamaModelsThread(QThread):
    """
    Thread per recuperare la lista dei modelli Ollama disponibili.
    """

    models_list = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            logging.info("Recupero modelli Ollama disponibili...")
            response = requests.get("http://localhost:11434/api/tags")
            response.raise_for_status()  # Lancia un'eccezione per risposte HTTP non riuscite
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            if not models:
                self.error_occurred.emit(
                    "Nessun modello Ollama trovato. Assicurati di averne scaricato almeno uno con 'ollama pull <nome_modello>'."
                )
                return

            logging.info(f"Modelli Ollama trovati: {models}")
            self.models_list.emit(models)
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(
                "Errore di connessione a Ollama. Assicurati che il servizio sia in esecuzione."
            )
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Errore nella richiesta a Ollama: {e}")
        except json.JSONDecodeError:
            self.error_occurred.emit("Risposta non valida da Ollama.")


class OllamaThread(QThread):
    """
    Thread per inviare una richiesta a Ollama e ricevere la risposta.
    """

    ollama_response = pyqtSignal(str)
    ollama_error = pyqtSignal(str)

    def __init__(self, prompt, model="llava:7b", parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.model = model

    def run(self):
        try:
            logging.info(f"Invio prompt a Ollama con il modello '{self.model}'...")

            headers = {"Content-Type": "application/json"}
            data = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": False,  # Semplifichiamo disabilitando lo streaming
            }

            response = requests.post(
                "http://localhost:11434/api/generate",
                headers=headers,
                data=json.dumps(data),
            )
            response.raise_for_status()

            # La risposta non è un singolo oggetto JSON, ma una sequenza di oggetti.
            # Se lo streaming è disabilitato, avremo un solo oggetto.
            data = response.json()

            full_response = data.get("response", "")

            if full_response:
                logging.info("Risposta da Ollama ricevuta con successo.")
                self.ollama_response.emit(full_response.strip())
            else:
                self.ollama_error.emit("Nessuna risposta valida da Ollama.")

        except requests.exceptions.ConnectionError:
            self.ollama_error.emit(
                "Errore di connessione. Assicurati che il servizio Ollama sia attivo."
            )
        except requests.exceptions.RequestException as e:
            self.ollama_error.emit(f"Errore nella richiesta Ollama: {e}")
        except json.JSONDecodeError:
            self.ollama_error.emit(
                "Risposta non valida da Ollama. Assicurati che il server sia configurato correttamente."
            )


if __name__ == "__main__":
    # Test del manager
    print("🔍 Test Ollama Manager...")

    if ollama_manager.check_ollama_running():
        print("✅ Ollama è in esecuzione")

        models = ollama_manager.get_available_models()
        print(f"📦 Modelli disponibili: {len(models)}")

        for model in models:
            print(f"  - {model['name']} ({model.get('size', 'N/A')} bytes)")

    else:
        print("❌ Ollama non è in esecuzione")
        print("💡 Avvio automatico...")

        if ollama_manager.start_ollama_service():
            print("✅ Ollama avviato con successo")
        else:
            print("❌ Impossibile avviare Ollama")
