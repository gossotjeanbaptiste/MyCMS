#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests du point d'entrée cms/web/server.py : environnement, instance unique, port occupé, lancement"""

import os
import socket

import flask
import pytest

import server
from desktop import startup
from publishing.git.git_manager import GitManager


@pytest.fixture
def opened(monkeypatch):
    """Pages que MyCMS ouvrirait dans le navigateur"""
    urls = []
    monkeypatch.setattr(server.webbrowser, "open", urls.append)
    return urls


def test_prepare_environment():
    resources, git_found = server.prepare_environment()
    assert resources.static_dir.is_dir() and resources.templates_dir.is_dir() and resources.icon_file.is_file()
    assert git_found is True and os.environ["GIT_PYTHON_REFRESH"]


def test_second_launch_opens_the_running_instance(monkeypatch, opened):
    monkeypatch.setattr(startup, "running_instance", lambda url: True)
    monkeypatch.setattr(flask.Flask, "run", lambda *a, **k: pytest.fail("le serveur ne doit pas démarrer"))
    server.main(port=5099, tray=False)
    assert opened == ["http://127.0.0.1:5099"]


def test_port_used_by_another_program(monkeypatch, opened):
    errors = []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "show_error", lambda message, logger: errors.append(message))
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        with pytest.raises(SystemExit) as stopped:
            server.main(port=busy.getsockname()[1], open_browser=False, tray=False)
    assert stopped.value.code == 1 and "déjà utilisé" in errors[0]


def test_normal_launch_with_auto_pull(monkeypatch, opened, isolated_home):
    from core.storage.config_manager import ConfigManager
    ConfigManager().set_auto_pull(True)
    pulls, runs = [], []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "port_free", lambda host, port: True)
    monkeypatch.setattr(GitManager, "pull", lambda self, path: pulls.append(path))
    monkeypatch.setattr(flask.Flask, "run", lambda app, host, port, threaded: runs.append((host, port)))
    server.main(port=5098, open_browser=False, tray=False)
    assert runs == [("127.0.0.1", 5098)]
    assert pulls == [str(isolated_home / "Rout-Art")]
    assert opened == []


def test_server_error_is_shown(monkeypatch, opened):
    errors = []
    monkeypatch.setattr(startup, "running_instance", lambda url: False)
    monkeypatch.setattr(startup, "port_free", lambda host, port: True)
    monkeypatch.setattr(startup, "show_error", lambda message, logger: errors.append(message))

    def crash(*args, **kwargs):
        raise RuntimeError("panne")

    monkeypatch.setattr(flask.Flask, "run", crash)
    with pytest.raises(SystemExit):
        server.main(port=5097, open_browser=False, tray=False)
    assert "panne" in errors[0]
