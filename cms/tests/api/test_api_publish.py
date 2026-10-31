#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : vérification avant publication, suivi de la mise en ligne, conflits"""

from conftest import git
from publishing import online


def test_checks_of_pages_to_publish(site_client, git_site):
    assert site_client.get("/api/checks").get_json() == {"success": True, "pages": [], "problems": []}
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace(b'href="#top"', b'href="#absente"'))
    data = site_client.get("/api/checks").get_json()
    assert data["pages"] == ["index.html"]
    assert data["problems"] == [{"page": "index.html", "line": 20, "message": "Ancre introuvable dans la page : #absente"}]


def test_checks_of_the_whole_site(site_client):
    data = site_client.get("/api/checks?scope=all").get_json()
    assert len(data["pages"]) == 5 and data["problems"] == []


def test_push_returns_the_published_pages(site_client, git_site):
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace(b"Offre", b"Promo"))
    result = site_client.post("/api/git/push", json={"message": "Promo"}).get_json()
    assert result["success"] and result["pages"] == ["index.html"]


def test_online(site_client, git_site, monkeypatch):
    served = {"https://exemple.github.io/": (git_site / "index.html").read_bytes()}
    monkeypatch.setattr(online, "fetch", served.get)
    data = site_client.get("/api/online?page=index.html&page=page/formations.html&page=../secret.html").get_json()
    assert data == {"success": True, "base_url": "https://exemple.github.io", "online": ["index.html"],
                    "waiting": ["page/formations.html"]}


def test_online_without_site_url(site_client, git_site):
    (git_site / "robots.txt").unlink()
    assert "URL du site introuvable" in site_client.get("/api/online?page=index.html").get_json()["error"]


def test_conflict_and_reset_to_remote(site_client, git_site, tmp_path):
    other = tmp_path / "autre"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(other))
    for folder, text in ((other, b"Offre de l'autre poste"), (git_site, b"Mon offre")):
        page = folder / "index.html"
        page.write_bytes(page.read_bytes().replace("Offre spéciale".encode("utf-8"), text))
    git(other, "commit", "-qam", "Autre poste")
    git(other, "push", "-q")
    result = site_client.post("/api/git/push", json={"message": "Mon offre"}).get_json()
    assert result["success"] is False and result["conflict"] is True
    reset = site_client.post("/api/git/reset-to-remote").get_json()
    assert reset["success"] and b"Offre de l'autre poste" in (git_site / "index.html").read_bytes()


def test_reset_without_repository(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path))
    assert client.post("/api/git/reset-to-remote").status_code == 500
