#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : installation d'une nouvelle version depuis le bouton de l'en-tête"""

import sys

import pytest

from api import shutdown
from core import updates
from desktop import installer

MSI = {"name": "MyCMS-99.0.0.msi", "url": "https://github.com/r/MyCMS-99.0.0.msi", "size": 3, "sha256": None}


@pytest.fixture
def release(monkeypatch):
    """Une version 99.0.0 publiée, avec son .msi"""
    monkeypatch.setattr(updates, "fetch_latest", lambda: {"tag": "v99.0.0", "url": "https://r", "installer": MSI})


@pytest.fixture
def frozen(monkeypatch):
    """Application installée (exe compilé par PyInstaller)"""
    monkeypatch.setattr(sys, "frozen", True, raising=False)


@pytest.fixture
def closing(monkeypatch):
    """Fermeture du processus remplacée : renvoie les fonctions programmées"""
    timers = []

    class FakeTimer:
        def __init__(self, delay, function, args):
            timers.append((delay, function, args))

        def start(self):
            pass

    monkeypatch.setattr(shutdown.threading, "Timer", FakeTimer)
    return timers


def test_auto_only_in_the_installed_application(client, release, monkeypatch):
    assert client.get("/api/update").get_json()["auto"] is False  # Depuis les sources
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    info = client.get("/api/update").get_json()
    assert info["auto"] is True and info["installer"] == MSI


def test_no_installer_means_no_auto(client, frozen, monkeypatch):
    monkeypatch.setattr(updates, "fetch_latest", lambda: {"tag": "v99.0.0", "url": "https://r", "installer": None})
    assert client.get("/api/update").get_json()["auto"] is False
    assert client.post("/api/update/install").status_code == 409


def test_install_refused(client, app, release, closing):
    assert client.post("/api/update/install").status_code == 400  # Depuis les sources : rien à remplacer
    marie = {"username": "Marie", "password": "mariepass", "confirm": "mariepass"}
    assert client.post("/api/users", json=marie).status_code == 200
    editor = app.test_client()
    editor.post("/api/auth/login", json={"username": "marie", "password": "mariepass"})
    assert editor.post("/api/update/install").status_code == 403
    assert closing == []


def test_install_downloads_launches_and_closes(client, release, frozen, closing, monkeypatch, tmp_path):
    launched = []
    monkeypatch.setattr(updates, "download", lambda msi, folder: tmp_path / msi["name"])
    monkeypatch.setattr(installer, "launch_installer", launched.append)
    response = client.post("/api/update/install")
    assert response.status_code == 200 and response.get_json()["version"] == "99.0.0"
    assert launched == [tmp_path / "MyCMS-99.0.0.msi"]
    assert closing and closing[0][0] == 0.5 and closing[0][1] is shutdown._exit_process
    assert client.get("/api/config").status_code == 401  # Session fermée


def test_failed_download_keeps_mycms_open(client, release, frozen, closing, monkeypatch):
    def broken(msi, folder):
        raise ValueError("le fichier reçu est incomplet ou abîmé")

    monkeypatch.setattr(updates, "download", broken)
    response = client.post("/api/update/install")
    assert response.status_code == 502 and "incomplet" in response.get_json()["error"]
    assert closing == [] and client.get("/api/config").status_code == 200
