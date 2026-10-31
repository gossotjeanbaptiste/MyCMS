#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixtures communes des tests de MyCMS.

Chaque test est isolé : dossier personnel temporaire (config, identifiants, logs dans ~/.mycms),
configuration Git temporaire (rien n'est ajouté au .gitconfig de l'utilisateur), pas de boîte de message.
"""

import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

CMS_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CMS_DIR / "source"), str(CMS_DIR / "web")]
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")

from site_builder import build_site  # noqa: E402

ADMIN = {"username": "Admin", "password": "adminpass", "confirm": "adminpass"}


def git(cwd, *args):
    """Commande Git ; retourne sa sortie"""
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Dossier personnel et configuration Git propres à chaque test"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("[user]\n\tname = MyCMS Tests\n\temail = tests@mycms.local\n"
                         "[init]\n\tdefaultBranch = main\n[core]\n\tautocrlf = false\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    # GitPython lit l'identité du poste dans ~/.gitconfig (pas GIT_CONFIG_GLOBAL) : la même, comme en vrai
    (home / ".gitconfig").write_text(gitconfig.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    # Sinon une vraie boîte de message Windows bloquerait le test
    import desktop.startup
    monkeypatch.setattr(desktop.startup, "show_error", lambda message, logger: logger.log(f"Erreur: {message}"))
    return home


@pytest.fixture
def logger(isolated_home):
    from core.logs.logger import Logger
    return Logger()


@pytest.fixture
def site(tmp_path):
    """Site de test, sans Git"""
    return build_site(tmp_path / "site")


@pytest.fixture
def git_site(site, tmp_path):
    """Site de test versionné, avec un remote bare local suivi par la branche main"""
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-q", str(remote))
    git(site, "init", "-q")
    git(site, "add", "-A")
    git(site, "commit", "-q", "-m", "Site initial")
    git(site, "remote", "add", "origin", str(remote))
    git(site, "push", "-q", "-u", "origin", "main")
    return site


@pytest.fixture
def app(isolated_home):
    from api import create_app
    from server import Resources
    web = CMS_DIR / "web"
    application = create_app(Resources(web / "static", web / "templates", CMS_DIR / "icon" / "logo.ico"), True)
    application.config["TESTING"] = True
    yield application
    preview = application.extensions["mycms"].preview
    if preview.is_running():
        preview.stop()


@pytest.fixture
def services(app):
    return app.extensions["mycms"]


@pytest.fixture
def client(app):
    """Client connecté avec le compte administrateur principal"""
    test_client = app.test_client()
    response = test_client.post("/api/auth/setup", json=ADMIN)
    assert response.status_code == 200, response.get_json()
    return test_client


@pytest.fixture
def site_client(client, services, git_site):
    """Client connecté, avec le site de test versionné comme repository"""
    services.config.set_repo_path(str(git_site))
    return client
