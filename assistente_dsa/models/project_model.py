#!/usr/bin/env python3
"""
Project Model - Modello dati per i progetti
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json


class ProjectModel:
    """Modello per rappresentare un progetto CogniFlow"""

    def __init__(self, name: str = "", data: Optional[Dict[str, Any]] = None):
        self.name = name
        self.data = data or {}
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.version = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Converte il progetto in dizionario per la serializzazione"""
        return {
            "name": self.name,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectModel":
        """Crea un progetto da un dizionario"""
        project = cls(name=data.get("name", ""), data=data.get("data", {}))
        project.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        project.last_modified = datetime.fromisoformat(
            data.get("last_modified", datetime.now().isoformat())
        )
        project.version = data.get("version", "1.0")
        return project

    def update_modified(self):
        """Aggiorna la data di ultima modifica"""
        self.last_modified = datetime.now()

    def is_empty(self) -> bool:
        """Verifica se il progetto è vuoto"""
        return not self.name and not self.data
