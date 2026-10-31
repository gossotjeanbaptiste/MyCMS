#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests des points d'entrée : cms/web/wsgi.py (application WSGI) et cms/web/server.py (lanceur, Waitress)"""

import os
import socket
import threading
import urllib.request

import flask
import pytest
from waitress import create_server

import server
import wsgi
from desktop import startup
from publishing.git.git_manager import GitManager


@pytest.fixture(autouse=True)
def served(monkeypatch):
    """Appels au serveur Waitress, sans le lancer vraiment (il bloquerait le test)"""
    calls = []
    monkeypatch.setattr(server, "serve", lambda app, **
                        options: calls.append((app, options)))
    return calls


@pytest.fixture
def opened(monkeypatch):
    """Pages que MyCMS ouvrirait dans le navigateur"""
    urls = []
    monkeypatch.setattr(server.webbrowser, "open", urls.append)
    return urls


# ======= wsgi.py =======

def test_prepare_environment():
    resources, git_found = wsgi.prepare_environment()
    assert resources.static_dir.is_dir(
    ) and resources.templates_dir.is_dir() and resources.icon_file.is_file()
    assert git_found is True and os.environ["GIT_PYTHON_REFRESH"]


def test_wsgi_app_is_built_on_demand():
    app = wsgi.app  # Convention des serveurs WSGI : wsgi:app
    assert isinstance(app, flask.Flask) and "mycms" in app.extensions
    with pytest.raises(AttributeError):
        wsgi.inconnu


def test_waitress_serves_the_application():
    """Le vrai serveur de production, sur un port libre : page de connexion, API, fichiers statiques"""
    waitress_server = create_server(
        wsgi.create_application(), host="127.0.0.1", port=0, threads=2)
    threading.Thread(target=waitress_server.run, daemon=True).start()
    base = f"http://127.0.0.1:{waitress_server.effective_port}"
    try:
        with urllib.request.urlopen(f"{base}/login", timeout=5) as response:
            assert response.status == 200 and b"auth-form" in response.read()
            assert response.headers["Server"] == "waitress"
        with urllib.request.urlopen(f"{base}/api/auth/state", timeout=5) as response:
            assert b'"setup_needed":true' in response.read()
        with urllib.request.urlopen(f"{base}/static/logo.png", timeout=5) as response:
            assert response.read()[:4] == b"\x89PNG"
    finally:
        waitress_server.close()


# ======= server.py =======

def test_normal_launch_serves_with_waitress(monkeypatch, opened, served, isolated_home):
    from core.storage.config_manager import ConfigManager
    ConfigManager().set_auto_pull(True)
    pulls = []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "port_free", lambda host, port: True)
    monkeypatch.setattr(GitManager, "pull", lambda self,
                        path: pulls.append(path))
    server.main(port=5098, open_browser=False, tray=False)
    app, options = served[0]
    assert isinstance(app, flask.Flask)
    assert options == {"host": "127.0.0.1", "port": 5098,
                       "threads": server.THREADS, "ident": "MyCMS"}
    assert server.THREADS >= 8
    assert pulls == [str(isolated_home / "mycms")]
    assert opened == []


def test_second_launch_opens_the_running_instance(monkeypatch, opened, served):
    monkeypatch.setattr(startup, "running_instance", lambda url: True)
    server.main(port=5099, tray=False)
    assert opened == ["http://127.0.0.1:5099"] and served == []


def test_port_used_by_another_program(monkeypatch, opened, served):
    errors = []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "show_error", lambda message,
                        logger: errors.append(message))
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        with pytest.raises(SystemExit) as stopped:
            server.main(port=busy.getsockname()[
                        1], open_browser=False, tray=False)
    assert stopped.value.code == 1 and "déjà utilisé" in errors[0] and served == [
    ]


def test_server_error_is_shown(monkeypatch, opened):
    errors = []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "port_free", lambda host, port: True)
    monkeypatch.setattr(startup, "show_error", lambda message,
                        logger: errors.append(message))

    def crash(app, **options):
        raise RuntimeError("panne")

    monkeypatch.setattr(server, "serve", crash)
    with pytest.raises(SystemExit):
        server.main(port=5097, open_browser=False, tray=False)
    assert "panne" in errors[0]
