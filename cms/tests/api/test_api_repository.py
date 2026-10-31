#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : onglet Git (vérifier, récupérer, pull, push, statut, annuler, ajouter)"""

from conftest import git


def edit(git_site):
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace(
        b"Offre sp\xc3\xa9ciale", "Offre modifiée".encode("utf-8")))


def test_verify(site_client, client, services, tmp_path):
    assert site_client.post("/api/git/verify").get_json()["success"] is True
    services.config.set_repo_path(str(tmp_path))
    assert client.post("/api/git/verify").get_json()["success"] is False


def test_status(site_client, client, services, tmp_path):
    edit(services.repo_path())
    data = site_client.get("/api/git/status").get_json()
    assert data["success"] and data["has_git"] and "[MODIFIER] index.html" in data["output"]
    services.config.set_repo_path(str(tmp_path))
    assert client.get("/api/git/status").get_json()["has_git"] is False


def test_push(site_client, git_site):
    assert site_client.post("/api/git/push", json={"message": "  "}).get_json()["error"] == \
        "Veuillez entrer un message de commit"
    edit(git_site)
    result = site_client.post(
        "/api/git/push", json={"message": "Offre du mois"}).get_json()
    assert result["success"] and "Push réussi" in result["message"]
    assert git(git_site, "log", "origin/main", "-1",
               "--format=%s") == "Offre du mois"


def test_pull(site_client, git_site, tmp_path):
    other = tmp_path / "autre"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(other))
    (other / "CNAME").write_text("www.mycms.fr", encoding="utf-8")
    git(other, "add", "-A")
    git(other, "commit", "-qm", "Domaine")
    git(other, "push", "-q")
    assert site_client.post("/api/git/pull").get_json()["success"]
    assert (git_site / "CNAME").exists()


def test_discard(site_client, git_site):
    edit(git_site)
    (git_site / "brouillon.html").write_text("x", encoding="utf-8")
    assert site_client.post("/api/git/discard", json={}
                            ).get_json()["removed"] == []
    assert (git_site / "brouillon.html").exists() and b"Offre sp\xc3\xa9ciale" in (
        git_site / "index.html").read_bytes()
    assert site_client.post(
        "/api/git/discard", json={"remove_untracked": True}).get_json()["removed"] == ["brouillon.html"]


def test_discard_without_repository(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path))
    assert client.post("/api/git/discard", json={}).status_code == 500


def test_add_untracked_files(site_client, git_site):
    (git_site / "nouveau.html").write_text("x", encoding="utf-8")
    assert site_client.post("/api/git/add").get_json()["success"]
    assert git(git_site, "status", "--porcelain") == "A  nouveau.html"


def test_add_outside_a_repository(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path))
    assert client.post("/api/git/add").status_code == 500


def test_clone(client, services, git_site, tmp_path):
    assert client.post("/api/git/clone", json={"url": " "}).status_code == 400
    occupied = tmp_path / "occupe"
    occupied.mkdir()
    (occupied / "fichier.txt").write_text("x", encoding="utf-8")
    response = client.post(
        "/api/git/clone", json={"url": str(tmp_path / "remote.git"), "path": str(occupied)})
    assert response.status_code == 400 and "n'est pas vide" in response.get_json()[
        "error"]
    destination = tmp_path / "copie"
    result = client.post("/api/git/clone", json={"url": str(
        tmp_path / "remote.git"), "path": str(destination)}).get_json()
    assert result["success"] and result["path"] == str(destination)
    assert (destination /
            "index.html").exists() and services.config.get_repo_path() == str(destination)


def test_clone_default_destination_and_failure(client, services, git_site, tmp_path, isolated_home):
    """Sans dossier choisi : dossier personnel / nom du repository, quelle que soit la forme de l'adresse"""
    result = client.post(
        "/api/git/clone", json={"url": str(tmp_path / "remote.git")}).get_json()
    assert result["path"] == str(isolated_home / "remote")
    file_url = (tmp_path / "remote.git").as_uri() + "/"
    assert client.post("/api/git/clone", json={"url": file_url}).get_json()[
        "error"].startswith("Le dossier existe déjà")
    failed = client.post(
        "/api/git/clone", json={"url": str(tmp_path / "absent.git"), "path": str(tmp_path / "x")})
    assert failed.status_code == 500 and "Erreur" in failed.get_json()["error"]
