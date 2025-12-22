#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Configuration - Stockage et récupération des paramètres
"""

import json
from pathlib import Path
import os
from typing import Any, Callable, Dict, Optional


class ConfigManager:
    """Gère la configuration persistante de l'application avec cache, validations et hooks"""

    # Schéma de validation pour chaque clé
    VALIDATION_SCHEMA = {
        "repo_path": {"type": str, "required": True},
        "auto_pull": {"type": bool, "required": True},
        "auto_refresh": {"type": bool, "required": True},
        "default_port": {"type": int, "required": True, "min": 1, "max": 65535},
        "theme": {"type": str, "required": True, "allowed": ["dark", "light"]},
        "window_width": {"type": int, "required": True, "min": 400},
        "window_height": {"type": int, "required": True, "min": 300},
    }

    def __init__(self):
        self.config_dir = Path.home() / ".rout_art_cms"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "repo_path": str(Path.home() / "Rout-Art"),
            "auto_pull": False,
            "auto_refresh": True,
            "default_port": 8000,
            "theme": "dark",
            "window_width": 1400,
            "window_height": 800
        }

        # Cache et hooks
        self._cache: Dict[str, Any] = {}
        self._cache_dirty = False
        self._on_before_change: Dict[str, list[Callable]] = {}
        self._on_after_change: Dict[str, list[Callable]] = {}

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

    def register_hook(self, key: str, hook_type: str, callback: Callable):
        """Enregistrer un hook avant ou après modification"""
        if hook_type not in ("before", "after"):
            raise ValueError("hook_type doit être 'before' ou 'after'")

        if hook_type == "before":
            if key not in self._on_before_change:
                self._on_before_change[key] = []
            self._on_before_change[key].append(callback)
        else:
            if key not in self._on_after_change:
                self._on_after_change[key] = []
            self._on_after_change[key].append(callback)

    def _execute_hooks(self, key: str, hook_type: str, old_value: Any, new_value: Any):
        """Exécuter les hooks enregistrés"""
        hooks = self._on_before_change.get(
            key, []) if hook_type == "before" else self._on_after_change.get(key, [])
        for hook in hooks:
            try:
                hook(key, old_value, new_value)
            except Exception as e:
                print(f"Erreur lors de l'exécution du hook {hook_type}: {e}")

    def load_config(self):
        """Charger la configuration depuis le fichier"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                    # Valider et nettoyer chaque clé chargée
                    for key, value in loaded_config.items():
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

        old_value = self._get_from_cache(key)

        # Hook before
        self._execute_hooks(key, "before", old_value, value)

        # Appliquer le changement
        self.config[key] = value
        self._cache[key] = value
        self._cache_dirty = True
        self.save_config()

        # Hook after
        self._execute_hooks(key, "after", old_value, value)

    def get_repo_path(self) -> str:
        """Récupérer le chemin du repository"""
        return self._get_from_cache("repo_path", self.default_config["repo_path"])

    def set_repo_path(self, path: str):
        """Définir le chemin du repository"""
        self._set_with_cache("repo_path", str(path))

    def get_auto_pull(self) -> bool:
        """Récupérer le paramètre de pull automatique"""
        return self._get_from_cache("auto_pull", self.default_config["auto_pull"])

    def set_auto_pull(self, value: bool):
        """Définir le pull automatique"""
        self._set_with_cache("auto_pull", bool(value))

    def get_auto_refresh(self) -> bool:
        """Récupérer le paramètre de rafraîchissement automatique"""
        return self._get_from_cache("auto_refresh", self.default_config["auto_refresh"])

    def set_auto_refresh(self, value: bool):
        """Définir le rafraîchissement automatique"""
        self._set_with_cache("auto_refresh", bool(value))

    def get_default_port(self) -> int:
        """Récupérer le port par défaut"""
        return self._get_from_cache("default_port", self.default_config["default_port"])

    def set_default_port(self, port: int):
        """Définir le port par défaut"""
        self._set_with_cache("default_port", int(port))

    def get_theme(self) -> str:
        """Récupérer le thème"""
        return self._get_from_cache("theme", self.default_config["theme"])

    def set_theme(self, theme: str):
        """Définir le thème"""
        self._set_with_cache("theme", theme)

    def get_window_dimensions(self) -> tuple[int, int]:
        """Récupérer les dimensions de la fenêtre"""
        width = self._get_from_cache(
            "window_width", self.default_config["window_width"])
        height = self._get_from_cache(
            "window_height", self.default_config["window_height"])
        return (width, height)

    def set_window_dimensions(self, width: int, height: int):
        """Définir les dimensions de la fenêtre"""
        self._set_with_cache("window_width", width)
        self._set_with_cache("window_height", height)

    def get_all_config(self) -> Dict[str, Any]:
        """Récupérer toute la configuration"""
        return self._cache.copy() if not self._cache_dirty else self.config.copy()

    def reset_to_defaults(self):
        """Réinitialiser aux paramètres par défaut"""
        self.config = self.default_config.copy()
        self._cache = self.config.copy()
        self.save_config()
