#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : gestion des comptes (administrateurs seulement)"""

import pytest

MARIE = {"username": "Marie", "password": "mariepass", "confirm": "mariepass"}


@pytest.fixture
def editor(client, app):
    """Client connecté avec le compte éditeur Marie"""
    assert client.post("/api/users", json=MARIE).status_code == 200
    marie = app.test_client()
    assert marie.post("/api/auth/login", json={"username": "marie", "password": "mariepass"}).status_code == 200
    return marie


def users(client):
    return {u["username"]: u for u in client.get("/api/users").get_json()["users"]}


def test_list_users(client):
    data = client.get("/api/users").get_json()
    assert data == {"users": [{"username": "Admin", "admin": True, "owner": True}], "me": "Admin"}


def test_add_user(client):
    assert client.post("/api/users", json={**MARIE, "confirm": "x"}).status_code == 400
    response = client.post("/api/users", json={**MARIE, "admin": True})
    assert response.get_json()["message"] == "Compte « Marie » créé" and users(client)["Marie"]["admin"]
    duplicate = client.post("/api/users", json={**MARIE, "username": "MARIE"})
    assert duplicate.status_code == 400 and "existe déjà" in duplicate.get_json()["error"]


def test_editor_cannot_manage_accounts(editor):
    assert editor.get("/api/auth/state").get_json()["admin"] is False
    for method, url in (("get", "/api/users"), ("post", "/api/users"), ("delete", "/api/users/Admin"),
                        ("post", "/api/users/Admin/role"), ("post", "/api/users/Admin/password")):
        response = getattr(editor, method)(url, json={})
        assert response.status_code == 403 and response.get_json()["error"] == "Réservé aux administrateurs"
    assert editor.get("/api/config").status_code == 200  # Le reste de l'application reste accessible


def test_reset_password_logs_the_user_out(client, editor):
    assert client.post("/api/users/Admin/password", json={"password": "x" * 8}).status_code == 400
    assert client.post("/api/users/Marie/password", json={"password": "court"}).status_code == 400
    assert client.post("/api/users/Marie/password", json={"password": "reset1234"}).status_code == 200
    assert editor.get("/api/config").status_code == 401


def test_roles(client, editor):
    assert client.post("/api/users/Admin/role", json={"admin": False}).status_code == 400
    assert client.post("/api/users/Marie/role", json={"admin": True}).get_json()["message"] == \
        "« Marie » est maintenant administrateur"
    assert editor.get("/api/users").status_code == 200
    # Même administratrice, Marie ne peut pas toucher à l'administrateur principal
    assert editor.post("/api/users/Admin/role", json={"admin": False}).status_code == 400
    assert editor.post("/api/users/Admin/password", json={"password": "x" * 8}).status_code == 400
    assert editor.delete("/api/users/Admin").status_code == 400
    assert editor.post("/api/users/Marie/role", json={"admin": False}).status_code == 200  # Se retirer : possible
    assert editor.get("/api/users").status_code == 403


def test_delete_user(client, editor, services):
    assert client.delete("/api/users/Admin").get_json()["error"] == "Vous ne pouvez pas supprimer votre propre compte"
    assert client.delete("/api/users/Inconnu").status_code == 400
    assert client.delete("/api/users/Marie").get_json()["users"] == [{"username": "Admin", "admin": True, "owner": True}]
    assert editor.get("/api/config").status_code == 401
    logs = "\n".join(services.logger.get_logs())
    assert "Compte éditeur « Marie » créé par Admin" in logs and "Compte « Marie » supprimé par Admin" in logs
