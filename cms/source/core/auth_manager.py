#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'authentification - Comptes de l'interface web
Le mot de passe n'est jamais stocké : seulement son empreinte (méthode par défaut de Werkzeug : scrypt, ou pbkdf2 avant Werkzeug 3).
Les administrateurs gèrent les comptes ; il en reste toujours au moins un.
"""

import secrets
import time

from werkzeug.security import check_password_hash, generate_password_hash

from core.auth_file import AuthFile

MIN_PASSWORD_LENGTH = 8
MAX_FAILURES = 5  # Tentatives avant blocage temporaire
LOCK_SECONDS = 30


class AuthManager:
    """Comptes : le premier, créé au premier lancement, est administrateur"""

    def __init__(self, config_dir):
        self._file = AuthFile(config_dir)
        self._failures = 0
        self._locked_until = 0.0

    @property
    def _users(self):
        return self._file.data["users"]

    def has_credentials(self):
        return bool(self._users)

    def secret_key(self):
        return self._file.data["secret_key"]

    def find(self, username):
        """Identifiant tel qu'enregistré (sans tenir compte des majuscules), ou None"""
        wanted = str(username or "").strip().casefold()
        return next((name for name in self._users if name.casefold() == wanted), None)

    def session_id(self, username):
        """Change à chaque nouveau mot de passe : les sessions ouvertes avant sont fermées"""
        user = self._users.get(username)
        return user["session_id"] if user else None

    def is_admin(self, username):
        user = self._users.get(username)
        return bool(user and user.get("admin"))

    def is_owner(self, username):
        """Administrateur principal (le premier compte) : ni rétrogradé, ni supprimé, ni réinitialisé par un autre"""
        user = self._users.get(username)
        return bool(user and user.get("owner"))

    def list_users(self):
        return [{"username": name, "admin": bool(user.get("admin")), "owner": bool(user.get("owner"))}
                for name, user in sorted(self._users.items(), key=lambda item: item[0].casefold())]

    # ======= Création et connexion =======

    @staticmethod
    def _check_password(password):
        if len(password) < MIN_PASSWORD_LENGTH:
            return f"Le mot de passe doit faire au moins {MIN_PASSWORD_LENGTH} caractères"
        return None

    def _set_password(self, username, password):
        self._users[username].update(
            password_hash=generate_password_hash(password),
            session_id=secrets.token_hex(16),
        )

    def _replace_password(self, username, new):
        error = self._check_password(new)
        if error:
            return error
        self._set_password(username, new)
        self._file.save()
        return None

    def add_user(self, username, password, admin=False, owner=False):
        """Ajouter un compte. Retourne un message d'erreur ou None"""
        username = str(username or "").strip()
        if not username:
            return "Veuillez entrer un identifiant"
        if self.find(username):
            return f"L'identifiant « {username} » existe déjà"
        error = self._check_password(password)
        if error:
            return error
        self._users[username] = {"admin": bool(admin or owner)}
        if owner:
            self._users[username]["owner"] = True
        self._set_password(username, password)
        self._file.save()
        return None

    def create(self, username, password):
        """Créer le premier compte, administrateur principal (premier lancement seulement)"""
        if self.has_credentials():
            return "Les identifiants existent déjà"
        return self.add_user(username, password, owner=True)

    def verify(self, username, password):
        """Vérifier les identifiants. Retourne (identifiant enregistré, None) ou (None, message d'erreur)"""
        remaining = self._locked_until - time.monotonic()
        if remaining > 0:
            return None, f"Trop de tentatives : réessayez dans {int(remaining) + 1} secondes"
        name = self.find(username)
        if name and check_password_hash(self._users[name]["password_hash"], password):
            self._failures = 0
            return name, None
        self._failures += 1
        if self._failures >= MAX_FAILURES:
            self._failures = 0
            self._locked_until = time.monotonic() + LOCK_SECONDS
            return None, f"Trop de tentatives : réessayez dans {LOCK_SECONDS} secondes"
        return None, "Identifiant ou mot de passe incorrect"

    def change_password(self, username, current, new):
        """Changer son propre mot de passe. Retourne un message d'erreur ou None"""
        user = self._users.get(username)
        if not user or not check_password_hash(user["password_hash"], current):
            return "Mot de passe actuel incorrect"
        return self._replace_password(username, new)

    # ======= Gestion des comptes (administrateurs) =======

    def reset_password(self, username, new):
        """Remplacer le mot de passe d'un compte, qui est déconnecté. Retourne un message d'erreur ou None"""
        if username not in self._users:
            return "Compte introuvable"
        if self.is_owner(username):
            return "Seul l'administrateur principal peut changer son mot de passe"
        return self._replace_password(username, new)

    def _other_admins(self, username):
        return [name for name, user in self._users.items() if user.get("admin") and name != username]

    def set_admin(self, username, admin):
        """Donner ou retirer le rôle d'administrateur. Retourne un message d'erreur ou None"""
        if username not in self._users:
            return "Compte introuvable"
        if not admin and self.is_owner(username):
            return "L'administrateur principal garde toujours ses accès"
        if not admin and not self._other_admins(username):
            return "Il faut au moins un administrateur : donnez d'abord ce rôle à un autre compte"
        self._users[username]["admin"] = bool(admin)
        self._file.save()
        return None

    def delete_user(self, username):
        """Supprimer un compte : ses sessions sont fermées. Retourne un message d'erreur ou None"""
        if username not in self._users:
            return "Compte introuvable"
        if self.is_owner(username):
            return "Le compte de l'administrateur principal ne peut pas être supprimé"
        if self.is_admin(username) and not self._other_admins(username):
            return "Impossible de supprimer le dernier administrateur"
        del self._users[username]
        self._file.save()
        return None
