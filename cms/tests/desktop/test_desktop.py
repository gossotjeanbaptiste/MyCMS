#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de desktop : serveur de prévisualisation, démarrage, choix d'un dossier, icône de notification"""

import http.server
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

import pytest

from conftest import free_port
from desktop import folder_picker, startup, tray
from desktop.server_manager import ServerManager


def wait_until(condition, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def preview(logger, site):
    """Serveur de prévisualisation lancé sur le site de test ; retourne (manager, url, messages)"""
    manager, port, messages = ServerManager(logger), free_port(), []
    thread = threading.Thread(target=manager.start, args=(str(site), port, messages.append, "window.mycms=1;"),
                              daemon=True)
    thread.start()
    assert wait_until(manager.is_running)
    yield manager, f"http://127.0.0.1:{port}", messages
    manager.stop()
    thread.join(timeout=5)


def get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8"), response.headers


# ======= Prévisualisation =======

def test_preview_serves_the_site_without_cache(preview):
    _, url, messages = preview
    body, headers = get(url + "/")
    assert "Bienvenue" in body and "window.mycms" not in body
    assert headers["Cache-Control"].startswith("no-store")
    assert any("Serveur démarré sur http://127.0.0.1" in m for m in messages)
    assert "Formations" in get(url + "/page/formations.html")[0]


def test_preview_script_is_injected_before_body_end(preview):
    _, url, _ = preview
    body, _ = get(url + "/?mycms-preview")
    assert "<script>window.mycms=1;</script></body>" in body
    assert "<script>window.mycms=1;</script>" in get(url + "/page/formations.html?mycms-preview")[0]
    with pytest.raises(urllib.error.HTTPError) as error:
        get(url + "/absente.html?mycms-preview")
    assert error.value.code == 404


def test_preview_stops(preview):
    manager, url, _ = preview
    assert manager.stop() and wait_until(lambda: not manager.is_running())
    with pytest.raises(urllib.error.URLError):
        get(url + "/")


def test_preview_refuses_missing_folder(logger, tmp_path):
    messages = []
    assert ServerManager(logger).start(str(tmp_path / "absent"), free_port(), messages.append) is False
    assert "n'existe pas" in messages[-1]


def test_preview_port_already_used(logger, site):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        messages = []
        ServerManager(logger).start(str(site), busy.getsockname()[1], messages.append)
    assert messages and messages[-1].startswith("❌")


# ======= Démarrage =======

def test_port_free():
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        assert startup.port_free("127.0.0.1", busy.getsockname()[1]) is False
    assert startup.port_free("127.0.0.1", free_port()) is True


def test_running_instance():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps({"setup_needed": False}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert startup.running_instance(f"http://127.0.0.1:{server.server_port}") is True
    finally:
        server.shutdown()
        server.server_close()
    assert startup.running_instance(f"http://127.0.0.1:{free_port()}") is False


# ======= Choix d'un dossier =======

def test_folder_picker_outside_windows(monkeypatch):
    monkeypatch.setattr(folder_picker.os, "name", "posix")
    assert "que sous Windows" in folder_picker.FolderPicker().choose()["error"]


@pytest.mark.skipif(os.name != "nt", reason="fenêtre de Windows")
def test_folder_picker_only_one_window(monkeypatch):
    picker = folder_picker.FolderPicker()
    picker._busy.acquire()
    assert picker.choose()["error"] == "Une fenêtre de sélection de dossier est déjà ouverte"
    picker._busy.release()
    monkeypatch.setattr(folder_picker, "_pick", lambda title, start, result: result.update(path=f"{start}|{title}"))
    assert picker.choose("Titre", "C:\\") == {"path": "C:\\|Titre"}


# ======= Icône de notification =======

def test_tray_without_pystray(monkeypatch, logger):
    monkeypatch.setitem(sys.modules, "pystray", None)
    assert tray.start_tray("http://127.0.0.1:5050", "logo.ico", logger) is None
    assert "pystray" in logger.get_logs()[-1]


def test_tray_menu_and_stop(monkeypatch, logger):
    import pystray
    from conftest import CMS_DIR
    started = threading.Event()

    class FakeIcon:
        def __init__(self, name, image, title, menu):
            self.items = [item.text for item in menu.items]

        def run(self):
            started.set()

        def stop(self):
            raise RuntimeError("déjà arrêtée")

    monkeypatch.setattr(pystray, "Icon", FakeIcon)
    icon = tray.start_tray("http://127.0.0.1:5050", CMS_DIR / "icon" / "logo.ico", logger)
    assert icon.items == ["Ouvrir MyCMS", "Quitter MyCMS…"] and started.wait(5)
    tray.stop_tray(icon)  # L'erreur de pystray ne remonte pas
    tray.stop_tray(None)
