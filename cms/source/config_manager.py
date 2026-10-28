#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Configuration - Stockage et récupération des paramètres
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from data_dir import data_dir


class ConfigManager:
    """Gère la configuration persistante de l'application avec cache et validations"""

    # Schéma de validation pour chaque clé
    VALIDATION_SCHEMA = {
        "repo_path": {"type": str, "required": True},
        "site_url": {"type": str, "required": False},
        "auto_pull": {"type": bool, "required": True},
        "show_guide": {"type": bool, "required": False},
        "default_port": {"type": int, "required": True, "min": 1, "max": 65535},
    }

    def __init__(self):
        self.config_dir = data_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "repo_path": str(Path.home() / "Rout-Art"),
            "site_url": "",
            "auto_pull": False,
            "show_guide": True,
            "default_port": 8000,
        }

        self._cache: Dict[str, Any] = {}
        self._cache_dirty = False

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.default_config.copy()
        self.load_config()

    def _validate_value(self, key: str, value: Any) -> tuple[bool, Optional[str]]:
        """Valider une valeur selon le schéma"""
        if key not in self.VALIDATION_SCHEMA:
            return False, f"Clé inconnue: {key}"

        schema = self.VALIDATION_SCHEMA[key]

        # Vérifier le type
        if not isinstance(value, schema["type"]):
            return False, f"{key} doit être de type {schema['type'].__name__}, reçu {type(value).__name__}"

        # Vérifier les limites numériques
        if schema["type"] in (int, float):
            if "min" in schema and value < schema["min"]:
                return False, f"{key} doit être >= {schema['min']}"
            if "max" in schema and value > schema["max"]:
                return False, f"{key} doit être <= {schema['max']}"

        # Vérifier les valeurs autorisées
        if "allowed" in schema and value not in schema["allowed"]:
            return False, f"{key} doit être l'une de {schema['allowed']}"

        return True, None

    def load_config(self):
        """Charger la configuration depuis le fichier"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                    # Valider et nettoyer chaque clé chargée
                    for key, value in loaded_config.items():
                        # Clé d'une ancienne version (thème, taille de fenêtre, auto_refresh…) : abandonnée
                        if key not in self.VALIDATION_SCHEMA:
                            continue
                        is_valid, error_msg = self._validate_value(key, value)
                        if not is_valid:
                            print(f"⚠️  Config invalide '{key}': {error_msg}")
                            print(
                                f"   → Utilisation de la valeur par défaut: {self.default_config.get(key)}")
                            self.config[key] = self.default_config.get(key)
                        else:
                            self.config[key] = value

                    self._cache = self.config.copy()
                    self._cache_dirty = False
                    self.save_config()  # Sauvegarder la config nettoyée
            else:
                # Premier lancement : le cache part des valeurs par défaut (sinon il resterait vide)
                self._cache = self.config.copy()
                self.save_config()
        except Exception as e:
            print(f"Erreur lors du chargement de la config: {e}")
            self.config = self.default_config.copy()
            self._cache = self.config.copy()

    def save_config(self):
        """Sauvegarder la configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self._cache_dirty = False
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la config: {e}")

    def _get_from_cache(self, key: str, default: Any = None) -> Any:
        """Récupérer depuis la cache"""
        if key in self._cache:
            return self._cache[key]
        return self.config.get(key, default)

    def _set_with_cache(self, key: str, value: Any):
        """Définir une valeur avec cache et validation"""
        # Validation
        is_valid, error_msg = self._validate_value(key, value)
        if not is_valid:
            raise ValueError(error_msg)

        self.config[key] = value
        self._cache[key] = value
        self._cache_dirty = True
        self.save_config()

    def get_repo_path(self) -> str:
        """Récupérer le chemin du repository"""
        return self._get_from_cache("repo_path", self.default_config["repo_path"])

    def set_repo_path(self, path: str):
        """Définir le chemin du repository"""
        self._set_with_cache("repo_path", str(path))

    def get_site_url(self) -> str:
        """Récupérer l'URL publique du site (vide = détection automatique)"""
        return self._get_from_cache("site_url", self.default_config["site_url"])

    def set_site_url(self, url: str):
        """Définir l'URL publique du site"""
        self._set_with_cache("site_url", str(url).strip())

    def get_auto_pull(self) -> bool:
        """Récupérer le paramètre de pull automatique"""
        return self._get_from_cache("auto_pull", self.default_config["auto_pull"])

    def set_auto_pull(self, value: bool):
        """Définir le pull automatique"""
        self._set_with_cache("auto_pull", bool(value))

    def get_show_guide(self) -> bool:
        """Afficher le guide d'utilisation au démarrage"""
        return self._get_from_cache("show_guide", self.default_config["show_guide"])

    def set_show_guide(self, value: bool):
        """Définir l'affichage du guide au démarrage"""
        self._set_with_cache("show_guide", bool(value))

    def get_default_port(self) -> int:
        """Récupérer le port par défaut"""
        return self._get_from_cache("default_port", self.default_config["default_port"])

    def set_default_port(self, port: int):
        """Définir le port par défaut"""
        self._set_with_cache("default_port", int(port))

    def get_all_config(self) -> Dict[str, Any]:
        """Récupérer toute la configuration (self.config reçoit chaque modification : il est toujours complet)"""
        return self.config.copy()

    def reset_to_defaults(self):
        """Réinitialiser aux paramètres par défaut"""
        self.config = self.default_config.copy()
        self._cache = self.config.copy()
        self.save_config()
