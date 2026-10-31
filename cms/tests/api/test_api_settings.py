#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : onglet Paramètres (configuration, choix d'un dossier) et onglet Logs"""

import pytest


def test_get_config(client, isolated_home):
    assert client.get("/api/config").get_json() == {
        "repo_path": str(isolated_home / "mycms"), "site_url": "", "auto_pull": False,
        "auto_update": True, "update_tried": "", "show_guide": True, "default_port": 8000}


def test_save_config(client, tmp_path):
    response = client.post("/api/config", json={"repo_path": str(tmp_path), "site_url": " https://exemple.fr ",
                                                "auto_pull": True, "auto_update": False, "show_guide": False,
                                                "default_port": "8123"})
    config = response.get_json()["config"]
    assert config == {"repo_path": str(tmp_path), "site_url": "https://exemple.fr", "auto_pull": True,
                      "auto_update": False, "update_tried": "", "show_guide": False, "default_port": 8123}
    assert client.get("/api/config").get_json() == config


def test_partial_save_keeps_other_settings(client):
    client.post("/api/config", json={"default_port": 9000})
    assert client.post(
        "/api/config", json={"show_guide": False}).get_json()["config"]["default_port"] == 9000


@pytest.mark.parametrize("body", [{"default_port": 0}, {"default_port": "abc"}, {"default_port": None}])
def test_invalid_settings_are_refused(client, body):
    response = client.post("/api/config", json=body)
    assert response.status_code == 400 and response.get_json()[
        "success"] is False
    assert client.get("/api/config").get_json()["default_port"] == 8000


def test_reset_config(client):
    client.post("/api/config",
                json={"default_port": 9000, "show_guide": False})
    assert client.post(
        "/api/config/reset").get_json()["config"]["default_port"] == 8000


def test_browse_folder(client, services, monkeypatch):
    calls = []

    def choose(title, start):
        calls.append((title, start))
        return {"path": "C:\\Sites\\MonSite"}

    monkeypatch.setattr(services.folder_picker, "choose", choose)
    response = client.post(
        "/api/browse-folder", json={"title": "Choisir le dossier du site", "start": "C:\\"})
    assert response.get_json() == {"success": True,
                                   "path": "C:\\Sites\\MonSite"}
    assert calls == [("Choisir le dossier du site", "C:\\")]
    # Sans corps : titre par défaut
    assert client.post("/api/browse-folder").status_code == 200
    assert calls[-1] == ("Choisir un dossier", "")


@pytest.mark.parametrize("result, status", [
    ({"error": "Une fenêtre de sélection de dossier est déjà ouverte"}, 409),
    ({"error": "La sélection de dossier n'est disponible que sous Windows"}, 500),
])
def test_browse_folder_errors(client, services, monkeypatch, result, status):
    monkeypatch.setattr(services.folder_picker, "choose",
                        lambda title, start: result)
    assert client.post("/api/browse-folder", json={}).status_code == status


def test_browse_folder_cancelled(client, services, monkeypatch):
    monkeypatch.setattr(services.folder_picker, "choose",
                        lambda title, start: {"cancelled": True})
    assert client.post("/api/browse-folder", json={}
                       ).get_json() == {"success": True, "cancelled": True}


def test_logs(client, services):
    services.logger.log("Message de test")
    assert services.logger.get_logs(
    )[-1] in client.get("/api/logs").get_json()["logs"]
    assert client.delete("/api/logs").get_json() == {"success": True}
    assert client.get("/api/logs").get_json()["logs"] == []


def test_update_check_is_done_once(client, monkeypatch):
    from core import updates
    calls = []
    monkeypatch.setattr(updates, "fetch_latest", lambda: calls.append(1) or {
                        "tag": "v99.0.0", "url": "https://r"})
    first = client.get("/api/update").get_json()
    assert first["available"] and first["latest"] == "99.0.0" and first["url"] == "https://r"
    assert client.get("/api/update").get_json() == first and calls == [1]


def test_favicon_is_public(app):
    response = app.test_client().get("/favicon.ico")
    assert response.status_code == 200 and response.mimetype == "image/x-icon" and response.data[
        :4] == b"\x00\x00\x01\x00"


def test_logs_since(client, services):
    total = client.get("/api/logs").get_json()["total"]
    services.logger.log("Nouvelle ligne")
    data = client.get(f"/api/logs?since={total}").get_json()
    assert data["reset"] is False and len(
        data["logs"]) == 1 and data["logs"][0].endswith("Nouvelle ligne")
    assert client.get(
        f"/api/logs?since={data['total']}").get_json()["logs"] == []
