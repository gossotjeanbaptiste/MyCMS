#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : sitemap, prévisualisation et fenêtre Quitter"""

import socket
import urllib.request

import pytest

from api import shutdown
from conftest import free_port


# ======= Sitemap =======

def test_sitemap_info(site_client, client, services, tmp_path):
    assert site_client.get("/api/sitemap").get_json() == {"success": True, "location": None,
                                                          "base_url": "https://exemple.github.io"}
    services.config.set_repo_path(str(tmp_path / "absent"))
    assert client.get("/api/sitemap").get_json()["location"] is None


def test_sitemap_generate(site_client, git_site):
    result = site_client.post("/api/sitemap").get_json()
    assert result["success"] and result["message"].startswith("Sitemap créé à la racine : 3 pages")
    assert site_client.get("/api/sitemap").get_json()["location"] == "sitemap.xml"
    assert site_client.post("/api/sitemap").get_json()["message"].startswith("Sitemap mis à jour")


def test_sitemap_without_site_url(site_client, git_site):
    (git_site / "robots.txt").unlink()
    response = site_client.post("/api/sitemap")
    # Le remote de test n'est pas sur GitHub : pas d'URL GitHub Pages à deviner
    assert response.status_code == 500 and "URL du site introuvable" in response.get_json()["error"]


# ======= Prévisualisation =======

@pytest.mark.parametrize("port, message", [("abc", "Le port doit être un nombre valide"),
                                           (70000, "Le port doit être entre 1 et 65535 (reçu: 70000)")])
def test_preview_invalid_port(site_client, port, message):
    assert site_client.post("/api/preview/start", json={"port": port}).get_json()["error"] == message


def test_preview_without_site(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path / "absent"))
    assert client.post("/api/preview/start", json={"port": free_port()}).get_json()["error"] == \
        "Le chemin du repository n'existe pas"


def test_preview_start_and_stop(site_client):
    port = free_port()
    started = site_client.post("/api/preview/start", json={"port": port}).get_json()
    assert started["success"] and started["running"] and started["port"] == port
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/?mycms-preview", timeout=5) as response:
        assert b"mycms-preview" in response.read()  # Script de l'aperçu en direct injecté
    again = site_client.post("/api/preview/start", json={"port": free_port()}).get_json()
    assert again["port"] == port  # Déjà lancé : rien ne change
    assert site_client.get("/api/preview").get_json()["running"] is True
    stopped = site_client.post("/api/preview/stop").get_json()
    assert stopped["running"] is False and stopped["logs"][-1] == "Serveur arrêté"


def test_preview_port_in_use(site_client):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        result = site_client.post("/api/preview/start", json={"port": busy.getsockname()[1]}).get_json()
    assert result["success"] is False and result["error"].startswith("❌")


# ======= Quitter =======

def test_quit_check(site_client, client, services, git_site, tmp_path):
    check = site_client.get("/api/quit/check").get_json()
    assert check["git"]["available"] and check["git"]["files"] == [] and check["preview_running"] is False
    (git_site / "nouveau.html").write_text("x", encoding="utf-8")
    assert site_client.get("/api/quit/check").get_json()["git"]["files"] == [{"state": "??", "path": "nouveau.html"}]
    services.git_found = False
    assert "Git est introuvable" in client.get("/api/quit/check").get_json()["git"]["message"]
    services.git_found = True
    services.config.set_repo_path(str(tmp_path))
    assert "pas un repository Git" in client.get("/api/quit/check").get_json()["git"]["message"]


def test_quit(site_client, services, monkeypatch):
    timers, exits, trays = [], [], []

    class FakeTimer:
        def __init__(self, delay, function, args):
            timers.append((delay, function, args))

        def start(self):
            pass

    monkeypatch.setattr(shutdown.threading, "Timer", FakeTimer)
    monkeypatch.setattr(shutdown.os, "_exit", exits.append)
    monkeypatch.setattr(shutdown, "stop_tray", trays.append)
    site_client.post("/api/preview/start", json={"port": free_port()})
    services.tray = "icône"
    assert site_client.post("/api/quit").get_json() == {"success": True}
    assert not services.preview.is_running()
    assert site_client.get("/api/config").status_code == 401  # Session fermée
    delay, function, args = timers[0]
    function(*args)  # Fin du processus, une fois la réponse envoyée
    assert delay == 0.5 and trays == ["icône"] and exits == [0]


def test_preview_status_since(site_client, services):
    services.preview_logs.append("GET /index.html")
    full = site_client.get("/api/preview").get_json()
    assert full["reset"] is True and full["logs"] == ["GET /index.html"] and full["total"] == 1
    services.preview_logs.append("GET /style.css")
    delta = site_client.get("/api/preview?since=1").get_json()
    assert delta == {"running": False, "port": None, "logs": ["GET /style.css"], "total": 2, "reset": False}
