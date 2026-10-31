#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : commits signés de la personne connectée, historique lisible"""

from git import Repo

from conftest import git
from core.auth_manager import AuthManager
from publishing.git_manager import GitManager
from publishing.history import entries


def edit(git_site, page="index.html", old="Offre spéciale", new="Offre du mois"):
    path = git_site / page
    path.write_bytes(path.read_bytes().replace(old.encode("utf-8"), new.encode("utf-8")))


def test_profile_and_commit_author(tmp_path):
    auth = AuthManager(tmp_path)
    auth.create("Admin", "adminpass")
    auth.add_user("Marie Claire", "mariepass")
    assert auth.profile("Admin") == {"name": "", "email": ""}
    assert auth.author("Admin") == ("Admin", "Admin@mycms.local")
    assert auth.author("Marie Claire") == ("Marie Claire", "Marie-Claire@mycms.local")
    assert auth.set_profile("Admin", "  Jean Dupont ", "jean@rout-art.fr") is None
    assert auth.author("Admin") == ("Jean Dupont", "jean@rout-art.fr")
    assert AuthManager(tmp_path).profile("Admin") == {"name": "Jean Dupont", "email": "jean@rout-art.fr"}
    assert auth.set_profile("Admin", "x", "pas-un-email") == "Adresse e-mail incorrecte"
    assert auth.set_profile("Admin", "x" * 101, "").startswith("Le nom doit faire au plus")
    assert auth.set_profile("Inconnu", "x", "") == "Compte introuvable"


def test_push_signed_by_the_logged_in_person(logger, git_site):
    edit(git_site)
    assert GitManager(logger).push(str(git_site), "Offre du mois", ("Marie Dupont", "marie@rout-art.fr"))["success"]
    commit = Repo(git_site).head.commit
    assert (commit.author.name, commit.author.email) == ("Marie Dupont", "marie@rout-art.fr")
    assert commit.committer.name == "MyCMS Tests"  # L'identité Git du poste envoie le commit


def test_history(logger, git_site):
    edit(git_site)
    GitManager(logger).push(str(git_site), "Offre du mois", ("Marie", "marie@mycms.local"))
    edit(git_site, "page/formations.html", "Formation moto.", "Moto.")
    (git_site / "style" / "style.css").write_text("p {}", encoding="utf-8")
    git(git_site, "commit", "-qam", "Pas encore publié")
    history = entries(Repo(git_site))
    assert [e["message"] for e in history] == ["Pas encore publié", "Offre du mois", "Site initial"]
    assert history[0]["pages"] == ["page/formations.html"] and history[0]["other_files"] == 1
    assert [e["published"] for e in history] == [False, True, True]
    assert history[1]["author"] == "Marie" and history[1]["pages"] == ["index.html"]
    assert len(history[2]["pages"]) == 7 and history[2]["other_files"] == 3  # Le site de test entier
    assert len(entries(Repo(git_site), limit=1)) == 1


def test_history_of_a_branch_never_published(git_site):
    git(git_site, "checkout", "-q", "-b", "brouillon")
    assert [e["published"] for e in entries(Repo(git_site))] == [False]


def test_history_errors(logger, tmp_path):
    assert GitManager(logger).history(str(tmp_path))["success"] is False
    git(tmp_path, "init", "-q")
    assert entries(Repo(tmp_path)) == []  # Aucun commit
