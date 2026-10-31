#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fichier des identifiants (auth.json) : lecture, écriture verrouillée, reprise de l'ancien format.

Format : {"secret_key": "...", "users": {"identifiant": {"password_hash", "session_id", "admin"}}}
Jusqu'à la v2.0.7, un seul compte : {"secret_key", "username", "password_hash", "session_id"}.
"""

import json
import secrets
from pathlib import Path

from core.storage.data_dir import lock_file, unlock_file


class AuthFile:
    """Contenu de auth.json, gardé en mémoire et réécrit à chaque changement"""

    def __init__(self, config_dir):
        self.path = Path(config_dir) / "auth.json"
        self.data = self._load()
        # Fichiers créés avant le verrouillage : verrouillés dès le démarrage
        lock_file(self.path)

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("secret_key", secrets.token_hex(32))
        users = data.get("users")
        data["users"] = users if isinstance(users, dict) else {}
        migrated = self._migrate(data)
        if self._ensure_owner(data) or migrated:
            self.data = data
            self.save()
        return data

    @staticmethod
    def _ensure_owner(data):
        """Le premier compte est l'administrateur principal : s'il n'est pas marqué, le marquer.
        Retourne vrai si le fichier a changé"""
        users = data["users"]
        if not users or any(user.get("owner") for user in users.values()):
            return False
        admins = [user for user in users.values() if user.get("admin")]
        first = admins[0] if admins else next(iter(users.values()))
        first.update(owner=True, admin=True)
        return True

    @staticmethod
    def _migrate(data):
        """Ancien compte unique : il devient l'administrateur principal. Retourne vrai s'il a été repris"""
        username = str(data.pop("username", "") or "").strip()
        password_hash = data.pop("password_hash", None)
        session_id = data.pop("session_id", None)
        if not (username and password_hash):
            return False
        data["users"].setdefault(username, {
            "password_hash": password_hash,
            "session_id": session_id or secrets.token_hex(16),
            "admin": True,
            "owner": True,
        })
        return True

    def save(self):
        """Écrire le fichier : il est verrouillé contre la modification, sauf pendant cette écriture"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        unlock_file(self.path)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        finally:
            lock_file(self.path)
