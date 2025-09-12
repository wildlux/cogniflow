#!/usr/bin/env python3
"""
Project Service - Gestione dei progetti
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal
from models.project_model import ProjectModel


class ProjectService(QObject):
    """
    Servizio per gestire il salvataggio e caricamento dei progetti
    """

    # Segnali
    project_saved = pyqtSignal(str)  # project_name
    project_loaded = pyqtSignal(str)  # project_name

    def __init__(self, projects_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        if projects_dir is None:
            # Usa la directory di default
            self.projects_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "Save", "mia_dispenda_progetti"
            )
        else:
            self.projects_dir = projects_dir

        # Assicura che la directory esista
        os.makedirs(self.projects_dir, exist_ok=True)
        self.logger.info(f"Project Service inizializzato - Directory: {self.projects_dir}")

    def save_project(self, project: ProjectModel) -> bool:
        """Salva un progetto su file"""
        if not project.name:
            self.logger.error("Nome progetto non specificato")
            return False

        try:
            # Crea il nome del file
            safe_name = self._sanitize_filename(project.name)
            file_path = os.path.join(self.projects_dir, f"{safe_name}.json")

            # Converte il progetto in dizionario
            project_data = project.to_dict()

            # Salva su file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Progetto salvato: {file_path}")
            self.project_saved.emit(project.name)
            return True

        except Exception as e:
            self.logger.error(f"Errore nel salvataggio del progetto: {e}")
            return False

    def load_project(self, project_name: str) -> Optional[ProjectModel]:
        """Carica un progetto da file"""
        try:
            safe_name = self._sanitize_filename(project_name)
            file_path = os.path.join(self.projects_dir, f"{safe_name}.json")

            if not os.path.exists(file_path):
                self.logger.warning(f"File progetto non trovato: {file_path}")
                return None

            # Carica il progetto
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # Crea l'oggetto progetto
            project = ProjectModel.from_dict(project_data)
            self.logger.info(f"Progetto caricato: {file_path}")
            self.project_loaded.emit(project.name)
            return project

        except Exception as e:
            self.logger.error(f"Errore nel caricamento del progetto: {e}")
            return None

    def delete_project(self, project_name: str) -> bool:
        """Elimina un progetto"""
        try:
            safe_name = self._sanitize_filename(project_name)
            file_path = os.path.join(self.projects_dir, f"{safe_name}.json")

            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Progetto eliminato: {file_path}")
                return True
            else:
                self.logger.warning(f"Progetto da eliminare non trovato: {file_path}")
                return False

        except Exception as e:
            self.logger.error(f"Errore nell'eliminazione del progetto: {e}")
            return False

    def get_project_list(self) -> List[str]:
        """Restituisce la lista dei progetti disponibili"""
        try:
            projects = []
            if os.path.exists(self.projects_dir):
                for file_name in os.listdir(self.projects_dir):
                    if file_name.endswith('.json'):
                        # Rimuovi l'estensione .json per ottenere il nome del progetto
                        project_name = file_name[:-5]  # Rimuove '.json'
                        projects.append(project_name)

            projects.sort()  # Ordina alfabeticamente
            return projects

        except Exception as e:
            self.logger.error(f"Errore nel recupero lista progetti: {e}")
            return []

    def project_exists(self, project_name: str) -> bool:
        """Verifica se un progetto esiste"""
        safe_name = self._sanitize_filename(project_name)
        file_path = os.path.join(self.projects_dir, f"{safe_name}.json")
        return os.path.exists(file_path)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizza il nome del file rimuovendo caratteri non validi"""
        import re
        # Sostituisce caratteri non alfanumerici con underscore
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        # Rimuove spazi multipli e underscore multipli
        sanitized = re.sub(r'[_\s]+', '_', sanitized)
        # Rimuove underscore agli estremi
        sanitized = sanitized.strip('_')
        return sanitized

    def get_project_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Restituisce informazioni su un progetto"""
        try:
            project = self.load_project(project_name)
            if project:
                return {
                    "name": project.name,
                    "created_at": project.created_at,
                    "last_modified": project.last_modified,
                    "version": project.version,
                    "data_size": len(json.dumps(project.data)) if project.data else 0
                }
            return None
        except Exception as e:
            self.logger.error(f"Errore nel recupero info progetto: {e}")
            return None