#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : « Mon compte » et historique de l'onglet Git"""

from git import Repo


def test_profile(client):
    assert client.get("/api/auth/profile").get_json() == {
        "name": "", "email": "", "author": "Admin <Admin@mycms.local>"}
    saved = client.post(
        "/api/auth/profile", json={"name": "Jean Dupont", "email": "jean@mycms.fr"}).get_json()
    assert saved == {"success": True, "message": "Profil enregistré"}
    assert client.get(
        "/api/auth/profile").get_json()["author"] == "Jean Dupont <jean@mycms.fr>"
    assert client.post("/api/auth/profile",
                       json={"name": "", "email": "faux"}).status_code == 400


def test_push_is_signed_by_the_logged_in_user(site_client, app, git_site):
    site_client.post(
        "/api/users", json={"username": "Marie", "password": "mariepass", "confirm": "mariepass"})
    marie = app.test_client()
    marie.post("/api/auth/login",
               json={"username": "Marie", "password": "mariepass"})
    marie.post("/api/auth/profile", json={"name": "Marie Dupont", "email": ""})
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace(b"Offre", b"Promo"))
    assert marie.post(
        "/api/git/push", json={"message": "Promo"}).get_json()["success"]
    assert Repo(git_site).head.commit.author.name == "Marie Dupont"
    entry = marie.get("/api/git/history").get_json()["entries"][0]
    assert entry["author"] == "Marie Dupont" and entry["published"] and entry["pages"] == [
        "index.html"]


def test_history_without_repository(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path))
    assert client.get(
        "/api/git/history").get_json() == {"success": True, "entries": []}


def test_commit_details_route(site_client, git_site):
    entry = site_client.get("/api/git/history").get_json()["entries"][0]
    details = site_client.get(f"/api/git/commit/{entry['hash']}").get_json()
    assert details["success"] and details["message"] == "Site initial" and len(
        details["pages"]) == 7
    assert site_client.get("/api/git/commit/1234567").status_code == 404
    assert site_client.get("/api/git/commit/pas-un-hash").status_code == 404
