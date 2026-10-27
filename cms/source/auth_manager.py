#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'authentification - Identifiants de l'interface web
Le mot de passe n'est jamais stocké : seulement son empreinte (scrypt, via Werkzeug)
"""

import json
import secrets
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from data_dir import lock_file, unlock_file

MIN_PASSWORD_LENGTH = 8
MAX_FAILURES = 5  # Tentatives avant blocage temporaire
LOCK_SECONDS = 30


class AuthManager:
    """Identifiants créés au premier lancement, dans le dossier de configuration"""

    def __init__(self, config_dir):
        self.auth_file = Path(config_dir) / "auth.json"
        self._data = self._load()
        # Fichiers créés avant le verrouillage : verrouillés dès le démarrage
        lock_file(self.auth_file)
        self._failures = 0
        self._locked_until = 0.0

    def _load(self):
        try:
            with open(self.auth_file, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("username") and data.get("password_hash"):
                return data
        except (OSError, ValueError):
            pass
        # Pas encore d'identifiants : la clé des sessions existe quand même
        return {"secret_key": secrets.token_hex(32)}

    def _save(self):
        """Écrire le fichier : il est verrouillé contre la modification, sauf pendant cette écriture"""
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        unlock_file(self.auth_file)
        try:
            with open(self.auth_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        finally:
            lock_file(self.auth_file)

    def has_credentials(self):
        return "password_hash" in self._data

    def username(self):
        return self._data.get("username")

    def secret_key(self):
        return self._data["secret_key"]

    def session_id(self):
        """Change à chaque nouveau mot de passe : les sessions ouvertes avant sont fermées"""
        return self._data.get("session_id")

    @staticmethod
    def _check_new(username, password):
        if not username.strip():
            return "Veuillez entrer un identifiant"
        if len(password) < MIN_PASSWORD_LENGTH:
            return f"Le mot de passe doit faire au moins {MIN_PASSWORD_LENGTH} caractères"
        return None

    def _set(self, username, password):
        self._data.update(
            username=username.strip(),
            password_hash=generate_password_hash(password),
            session_id=secrets.token_hex(16),
        )
        self._save()

    def create(self, username, password):
        """Créer les identifiants (premier lancement seulement). Retourne un message d'erreur ou None"""
        if self.has_credentials():
            return "Les identifiants existent déjà"
        error = self._check_new(username, password)
        if error:
            return error
        self._set(username, password)
        return None

    def verify(self, username, password):
        """Vérifier les identifiants. Retourne un message d'erreur ou None"""
        remaining = self._locked_until - time.monotonic()
        if remaining > 0:
            return f"Trop de tentatives : réessayez dans {int(remaining) + 1} secondes"
        if (self.has_credentials() and username.strip() == self._data["username"]
                and check_password_hash(self._data["password_hash"], password)):
            self._failures = 0
            return None
        self._failures += 1
        if self._failures >= MAX_FAILURES:
            self._failures = 0
            self._locked_until = time.monotonic() + LOCK_SECONDS
            return f"Trop de tentatives : réessayez dans {LOCK_SECONDS} secondes"
        return "Identifiant ou mot de passe incorrect"

    def change_password(self, current, new):
        """Changer le mot de passe. Retourne un message d'erreur ou None"""
        if not check_password_hash(self._data.get("password_hash", ""), current):
            return "Mot de passe actuel incorrect"
        error = self._check_new(self._data["username"], new)
        if error:
            return error
        self._set(self._data["username"], new)
        return None
