#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Configuration - Stockage et récupération des paramètres (config.json)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.storage.data_dir import data_dir


class ConfigManager:
    """Configuration persistante, validée à la lecture et à chaque modification"""

    # Type attendu de chaque clé, et bornes des nombres
    VALIDATION_SCHEMA = {
        "repo_path": {"type": str},
        "site_url": {"type": str},
        "auto_pull": {"type": bool},
        "show_guide": {"type": bool},
        "default_port": {"type": int, "min": 1, "max": 65535},
    }

    def __init__(self):
        self.config_dir = data_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            # Un dossier dédié : le dossier personnel entier serait parcouru à la recherche de pages
            "repo_path": str(Path.home() / "mycms"),
            "site_url": "",
            "auto_pull": False,
            "show_guide": True,
            "default_port": 8000,
        }
        self.config = self.default_config.copy()
        self.load_config()

    def _validate_value(self, key: str, value: Any) -> tuple[bool, Optional[str]]:
        """Valider une valeur selon le schéma"""
        if key not in self.VALIDATION_SCHEMA:
            return False, f"Clé inconnue: {key}"
        schema = self.VALIDATION_SCHEMA[key]
        if not isinstance(value, schema["type"]):
            return False, f"{key} doit être de type {schema['type'].__name__}, reçu {type(value).__name__}"
        if "min" in schema and value < schema["min"]:
            return False, f"{key} doit être >= {schema['min']}"
        if "max" in schema and value > schema["max"]:
            return False, f"{key} doit être <= {schema['max']}"
        return True, None

    def load_config(self):
        """Charger la configuration depuis le fichier, puis l'enregistrer nettoyée (ou créée au premier lancement)"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                for key, value in loaded_config.items():
                    # Clé d'une ancienne version (thème, taille de fenêtre, auto_refresh…) : abandonnée
                    if key not in self.VALIDATION_SCHEMA:
                        continue
                    is_valid, error_msg = self._validate_value(key, value)
                    if is_valid:
                        self.config[key] = value
                    else:
                        # Sans emoji : il ferait planter une console non UTF-8 (run.bat)
                        print(f"Config invalide '{key}': {error_msg} - valeur par défaut utilisée")
            self.save_config()
        except Exception as e:
            print(f"Erreur lors du chargement de la config: {e}")
            self.config = self.default_config.copy()

    def save_config(self):
        """Sauvegarder la configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la config: {e}")

    def _set(self, key: str, value: Any):
        """Modifier une valeur après validation, puis enregistrer"""
        is_valid, error_msg = self._validate_value(key, value)
        if not is_valid:
            raise ValueError(error_msg)
        self.config[key] = value
        self.save_config()

    def get_repo_path(self) -> str:
        """Récupérer le chemin du repository"""
        return self.config["repo_path"]

    def set_repo_path(self, path: str):
        """Définir le chemin du repository"""
        self._set("repo_path", str(path))

    def get_site_url(self) -> str:
        """Récupérer l'URL publique du site (vide = détection automatique)"""
        return self.config["site_url"]

    def set_site_url(self, url: str):
        """Définir l'URL publique du site"""
        self._set("site_url", str(url).strip())

    def get_auto_pull(self) -> bool:
        """Récupérer le paramètre de pull automatique"""
        return self.config["auto_pull"]

    def set_auto_pull(self, value: bool):
        """Définir le pull automatique"""
        self._set("auto_pull", bool(value))

    def set_show_guide(self, value: bool):
        """Définir l'affichage du guide au démarrage"""
        self._set("show_guide", bool(value))

    def set_default_port(self, port: int):
        """Définir le port par défaut"""
        self._set("default_port", int(port))

    def get_all_config(self) -> Dict[str, Any]:
        """Toute la configuration (show_guide, default_port… sont lus par l'interface à partir d'ici)"""
        return self.config.copy()

    def reset_to_defaults(self):
        """Réinitialiser aux paramètres par défaut"""
        self.config = self.default_config.copy()
        self.save_config()
