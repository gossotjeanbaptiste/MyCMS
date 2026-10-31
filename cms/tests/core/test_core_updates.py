#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de core : recherche d'une nouvelle version sur GitHub, anciens mots de passe après la mise à jour de Werkzeug"""

import hashlib
import http.server
import json
import threading

import pytest
from werkzeug.security import check_password_hash

from core import updates
from version import VERSION


@pytest.mark.parametrize("text, expected", [("v2.1.5", (2, 1, 5)), ("10.0.1", (10, 0, 1)), ("v2.1", None),
                                            ("nightly", None), (None, None)])
def test_parse_version(text, expected):
    assert updates.parse_version(text) == expected


@pytest.mark.parametrize("tag, available", [("v2.2.0", True), ("v2.1.10", True), ("v2.1.5", False),
                                            ("v2.0.9", False), ("nightly", False)])
def test_update_info(tag, available):
    info = updates.update_info("2.1.5", {"tag": tag, "url": "https://github.com/x/releases/tag/" + tag})
    assert info["available"] is available and info["current"] == "2.1.5"
    assert info["latest"] == (tag.lstrip("v") if available else None)


def test_no_release_means_no_update():
    assert updates.update_info(VERSION, None) == {"available": False, "current": VERSION, "latest": None,
                                                  "url": None, "installer": None}


def serve(body):
    """Serveur local qui répond body à toute requête ; renvoie (serveur, adresse)"""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_fetch_latest(monkeypatch):
    server, url = serve(json.dumps({"tag_name": "v9.0.0", "html_url": "https://github.com/r/releases/tag/v9.0.0",
                                    "assets": []}).encode())
    monkeypatch.setattr(updates, "RELEASES_URL", url + "/latest")
    try:
        assert updates.fetch_latest() == {"tag": "v9.0.0", "url": "https://github.com/r/releases/tag/v9.0.0",
                                          "installer": None}
    finally:
        server.shutdown()
        server.server_close()
    assert updates.fetch_latest() is None  # Plus de serveur : rien n'est signalé


def test_installer_asset():
    assets = [{"name": "MyCMS.exe", "browser_download_url": "https://x/MyCMS.exe", "size": 1},
              {"name": "MyCMS-9.0.0.msi", "browser_download_url": "https://x/MyCMS-9.0.0.msi", "size": 5,
               "digest": "sha256:ABC"}]
    assert updates.installer_asset(assets) == {"name": "MyCMS-9.0.0.msi", "url": "https://x/MyCMS-9.0.0.msi",
                                               "size": 5, "sha256": "ABC"}
    assert updates.installer_asset(assets[:1]) is None and updates.installer_asset(None) is None
    assert updates.installer_asset([{**assets[1], "digest": None}])["sha256"] is None  # Ancienne release


def test_download_checks_size_and_digest(tmp_path):
    content = b"installeur"
    server, url = serve(content)
    msi = {"name": "../MyCMS-9.0.0.msi", "url": url + "/a.msi", "size": len(content),
           "sha256": hashlib.sha256(content).hexdigest().upper()}
    try:
        path = updates.download(msi, tmp_path / "maj")
        assert path == tmp_path / "maj" / "MyCMS-9.0.0.msi" and path.read_bytes() == content  # Pas de « ../ »
        for wrong in ({"size": 3}, {"sha256": "0" * 64}):
            with pytest.raises(ValueError):
                updates.download({**msi, **wrong}, tmp_path / "maj")
            assert not path.exists()  # Fichier abîmé supprimé
    finally:
        server.shutdown()
        server.server_close()


def test_installer_command():
    from desktop.installer import installer_command
    assert installer_command("C:/t/MyCMS.msi") == ["msiexec", "/i", "C:/t/MyCMS.msi", "/passive", "LAUNCHAPP=1"]


def test_old_pbkdf2_passwords_still_work():
    """Werkzeug 3 enregistre en scrypt, mais les comptes créés avec Werkzeug 2 (pbkdf2) se connectent toujours"""
    old_hash = ("pbkdf2:sha256:600000$qezxFN3O6KbZicdz$"
                "25f2041f5ac7f4ed5d172a0d431be86db922ee367243c90e58f9d05861af9d1c")
    assert check_password_hash(old_hash, "motdepasse") is True
    assert check_password_hash(old_hash, "mauvais") is False
