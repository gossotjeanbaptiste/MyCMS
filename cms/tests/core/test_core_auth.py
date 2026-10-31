#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de core : comptes (AuthManager) et fichier auth.json (AuthFile)"""

import json

import pytest
from werkzeug.security import generate_password_hash

from core.auth import auth_manager
from core.auth.auth_manager import AuthManager
from core.storage.data_dir import unlock_file


def write_auth(directory, data):
    path = directory / "auth.json"
    unlock_file(path)
    path.write_text(json.dumps(data), encoding="utf-8")


def read_auth(directory):
    return json.loads((directory / "auth.json").read_text(encoding="utf-8"))


@pytest.fixture
def auth(tmp_path):
    manager = AuthManager(tmp_path)
    assert manager.create("Admin", "adminpass") is None
    return manager


def test_first_account_is_owner(tmp_path):
    manager = AuthManager(tmp_path)
    assert not manager.has_credentials()
    assert manager.create("  Admin ", "court") == "Le mot de passe doit faire au moins 8 caractères"
    assert manager.create("", "adminpass") == "Veuillez entrer un identifiant"
    assert manager.create("Admin", "adminpass") is None
    assert manager.is_owner("Admin") and manager.is_admin("Admin")
    assert manager.create("Autre", "adminpass") == "Les identifiants existent déjà"


def test_password_is_never_stored_in_clear(auth, tmp_path):
    stored = (tmp_path / "auth.json").read_text(encoding="utf-8")
    assert "adminpass" not in stored
    # Méthode par défaut de Werkzeug : scrypt depuis la 3.0, pbkdf2 avant
    assert read_auth(tmp_path)["users"]["Admin"]["password_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_secret_key_survives_restart(auth, tmp_path):
    assert AuthManager(tmp_path).secret_key() == auth.secret_key()


def test_legacy_single_account_is_migrated(tmp_path):
    write_auth(tmp_path, {"secret_key": "k", "username": "Alice",
                          "password_hash": generate_password_hash("motdepasse"), "session_id": "s1"})
    manager = AuthManager(tmp_path)
    assert read_auth(tmp_path) == {"secret_key": "k", "users": {"Alice": {
        "password_hash": read_auth(tmp_path)["users"]["Alice"]["password_hash"],
        "session_id": "s1", "admin": True, "owner": True}}}
    assert manager.verify("alice", "motdepasse") == ("Alice", None)


def test_file_without_owner_gets_one(tmp_path):
    write_auth(tmp_path, {"secret_key": "k", "users": {
        "ed": {"admin": False, "password_hash": "h", "session_id": "1"},
        "chef": {"admin": True, "password_hash": "h", "session_id": "2"}}})
    assert AuthManager(tmp_path).is_owner("chef")
    assert read_auth(tmp_path)["users"]["chef"]["owner"] is True


def test_corrupted_file_starts_empty(tmp_path):
    write_auth(tmp_path, ["pas", "un", "objet"])
    manager = AuthManager(tmp_path)
    assert not manager.has_credentials() and manager.secret_key()


def test_login_is_case_insensitive(auth):
    assert auth.verify(" ADMIN ", "adminpass") == ("Admin", None)
    assert auth.verify("Admin", "mauvais") == (None, "Identifiant ou mot de passe incorrect")
    assert auth.verify("Inconnu", "adminpass")[0] is None


def test_too_many_failures_lock_login(auth, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(auth_manager.time, "monotonic", lambda: clock[0])
    for _ in range(auth_manager.MAX_FAILURES - 1):
        auth.verify("Admin", "mauvais")
    assert "Trop de tentatives" in auth.verify("Admin", "mauvais")[1]
    assert "Trop de tentatives" in auth.verify("Admin", "adminpass")[1]  # Même le bon mot de passe
    clock[0] += auth_manager.LOCK_SECONDS + 1
    assert auth.verify("Admin", "adminpass") == ("Admin", None)


def test_add_user_rules(auth):
    assert auth.add_user("marie", "mariepass") is None
    assert not auth.is_admin("marie") and not auth.is_owner("marie")
    assert auth.add_user("MARIE", "mariepass") == "L'identifiant « MARIE » existe déjà"
    assert auth.add_user("paul", "court").startswith("Le mot de passe")
    assert auth.add_user("chef", "chefpass", admin=True) is None and auth.is_admin("chef")
    assert [u["username"] for u in auth.list_users()] == ["Admin", "chef", "marie"]


def test_new_password_closes_sessions(auth):
    auth.add_user("marie", "mariepass")
    before = auth.session_id("marie")
    assert auth.change_password("marie", "faux", "nouveau123") == "Mot de passe actuel incorrect"
    assert auth.change_password("marie", "mariepass", "nouveau123") is None
    assert auth.session_id("marie") != before
    assert auth.reset_password("marie", "reset1234") is None
    assert auth.verify("marie", "reset1234")[0] == "marie"
    assert auth.reset_password("inconnu", "reset1234") == "Compte introuvable"


def test_owner_is_protected(auth):
    assert auth.set_admin("Admin", False) == "L'administrateur principal garde toujours ses accès"
    assert auth.delete_user("Admin") == "Le compte de l'administrateur principal ne peut pas être supprimé"
    assert auth.reset_password("Admin", "x" * 8).startswith("Seul l'administrateur principal")
    assert auth.change_password("Admin", "adminpass", "nouveau123") is None  # Lui-même : possible


def test_roles_and_deletion(auth):
    auth.add_user("chef", "chefpass", admin=True)
    auth.add_user("marie", "mariepass")
    assert auth.set_admin("marie", True) is None and auth.is_admin("marie")
    assert auth.set_admin("chef", False) is None and not auth.is_admin("chef")
    assert auth.delete_user("marie") is None and auth.session_id("marie") is None
    assert auth.delete_user("marie") == "Compte introuvable"
    assert auth.set_admin("inconnu", True) == "Compte introuvable"


def test_last_admin_rule_without_owner(tmp_path):
    """Fichier modifié à la main où l'administrateur n'est pas principal : il reste protégé comme dernier admin"""
    write_auth(tmp_path, {"secret_key": "k", "users": {
        "boss": {"admin": True, "owner": True, "password_hash": "h", "session_id": "1"},
        "chef": {"admin": True, "password_hash": "h", "session_id": "2"}}})
    manager = AuthManager(tmp_path)
    manager._users["boss"]["admin"] = False  # Situation impossible par l'interface
    assert manager.set_admin("chef", False).startswith("Il faut au moins un administrateur")
    assert manager.delete_user("chef") == "Impossible de supprimer le dernier administrateur"
