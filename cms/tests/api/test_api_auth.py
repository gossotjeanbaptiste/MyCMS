#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : connexion, sessions, pages de l'interface"""

import pytest

from conftest import ADMIN


def state(client):
    return client.get("/api/auth/state").get_json()


# ======= Accès sans être connecté =======

def test_login_required(app):
    anonymous = app.test_client()
    assert anonymous.get("/").headers["Location"].endswith("/login")
    response = anonymous.get("/api/config")
    assert response.status_code == 401 and "reconnectez-vous" in response.get_json()["error"]


@pytest.mark.parametrize("path", ["/login", "/static/scripts/login.js", "/static/style.css", "/static/logo.png",
                                  "/api/auth/state"])
def test_public_paths(app, path):
    assert app.test_client().get(path).status_code == 200


def test_static_files_need_login(app):
    assert app.test_client().get("/static/scripts/main.js").status_code == 302


# ======= Premier lancement =======

def test_setup_creates_owner_and_opens_session(app):
    anonymous = app.test_client()
    assert state(anonymous) == {"setup_needed": True, "logged_in": False, "username": None, "admin": False}
    bad = anonymous.post("/api/auth/setup", json={**ADMIN, "confirm": "autre"})
    assert bad.status_code == 400 and "ne correspondent pas" in bad.get_json()["error"]
    assert anonymous.post("/api/auth/setup", json=ADMIN).status_code == 200
    assert state(anonymous) == {"setup_needed": False, "logged_in": True, "username": "Admin", "admin": True}
    again = app.test_client().post("/api/auth/setup", json={**ADMIN, "username": "Pirate"})
    assert again.status_code == 400 and again.get_json()["error"] == "Les identifiants existent déjà"


def test_login_page_redirects_when_logged_in(client):
    assert client.get("/login").headers["Location"].endswith("/")


# ======= Connexion, déconnexion =======

def test_login_and_logout(client, app, services):
    other = app.test_client()
    failed = other.post("/api/auth/login", json={"username": "admin", "password": "faux"})
    assert failed.status_code == 401 and failed.get_json()["error"] == "Identifiant ou mot de passe incorrect"
    assert other.post("/api/auth/login", json={"username": "ADMIN", "password": "adminpass"}).status_code == 200
    assert state(other)["username"] == "Admin"
    assert other.post("/api/auth/logout").status_code == 200
    assert not state(other)["logged_in"] and state(client)["logged_in"]
    logs = "\n".join(services.logger.get_logs())
    assert "Échec de connexion" in logs and "Connexion de Admin" in logs and "Déconnexion de Admin" in logs


def test_restart_requires_new_login(client, services):
    """v2.0.3 : la clé des cookies ne change pas, mais un relancement ferme les sessions"""
    services.boot_id = "nouveau-demarrage"
    assert not state(client)["logged_in"]


def test_change_password(client, app):
    other = app.test_client()
    other.post("/api/auth/login", json={"username": "Admin", "password": "adminpass"})
    mismatch = client.post("/api/auth/password", json={"current": "adminpass", "new": "nouveau123", "confirm": "x"})
    assert mismatch.status_code == 400
    wrong = client.post("/api/auth/password", json={"current": "faux", "new": "nouveau123", "confirm": "nouveau123"})
    assert wrong.get_json()["error"] == "Mot de passe actuel incorrect"
    done = client.post("/api/auth/password", json={"current": "adminpass", "new": "nouveau123", "confirm": "nouveau123"})
    assert done.get_json() == {"success": True, "message": "Mot de passe modifié"}
    assert state(client)["logged_in"] and not state(other)["logged_in"]  # Les autres sessions sont fermées


# ======= Pages de l'interface =======

def test_index_contains_every_tab_and_dialog(client):
    page = client.get("/").get_data(as_text=True)
    for element in ('id="tab-git"', 'id="tab-editor"', 'id="tab-preview"', 'id="tab-settings"', 'id="tab-logs"',
                    'id="guide-dialog"', 'id="quit-dialog"', 'id="category-bar"', 'id="users-card"',
                    'src="/static/logo-wide.png"'):
        assert element in page


def test_static_files_are_served(client):
    response = client.get("/static/scripts/main.js")
    assert response.status_code == 200 and b"initCategories" in response.data
    assert client.get("/static/absent.js").status_code == 404
