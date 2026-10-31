#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : opérations Git (vrais dépôts, remote bare local)"""

import os
import shutil

import pytest

from conftest import git
from publishing.git.git_manager import GitManager


@pytest.fixture
def manager(logger):
    return GitManager(logger)


def remote_log(git_site):
    return git(git_site, "log", "origin/main", "--format=%s")


def edit(git_site, text="Modifié"):
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace(b"Offre sp\xc3\xa9ciale", text.encode("utf-8")))


def test_verify_repo(manager, git_site, tmp_path):
    result = manager.verify_repo(str(git_site))
    assert result["valid"] and "Branche: main" in result["message"]
    assert not manager.verify_repo(str(tmp_path))["valid"]


def test_safe_directory_goes_to_test_config_only(manager, git_site):
    manager.verify_repo(str(git_site))
    assert "safe" in open(os.environ["GIT_CONFIG_GLOBAL"], encoding="utf-8").read()


def test_pending_lists_files_and_commits(manager, git_site):
    assert manager.pending(str(git_site)) == {"success": True, "branch": "main", "files": [], "ahead": 0,
                                              "has_upstream": True}
    edit(git_site)
    (git_site / "nouveau.html").write_text("x", encoding="utf-8")
    files = manager.pending(str(git_site))["files"]
    assert {"state": "M", "path": "index.html"} in files and {"state": "??", "path": "nouveau.html"} in files
    git(git_site, "commit", "-qam", "Local")
    assert manager.pending(str(git_site))["ahead"] == 1


def test_push_commits_and_sends(manager, git_site):
    edit(git_site)
    result = manager.push(str(git_site), "Nouvelle offre")
    assert result["success"] and "Push réussi" in result["message"]
    git(git_site, "fetch", "-q")
    assert remote_log(git_site).splitlines()[0] == "Nouvelle offre"
    assert manager.push(str(git_site), "Rien")["message"].endswith("Aucune modification à pousser")


def test_push_sends_commits_left_behind(manager, git_site, tmp_path):
    shutil.move(tmp_path / "remote.git", tmp_path / "ailleurs.git")  # Remote injoignable
    edit(git_site)
    failed = manager.push(str(git_site), "Première tentative")
    assert not failed["success"] and "Erreur Git" in failed["message"]
    assert manager.pending(str(git_site))["ahead"] == 1  # Le commit est gardé
    shutil.move(tmp_path / "ailleurs.git", tmp_path / "remote.git")
    (git_site / "autre.html").write_text("<p>autre</p>", encoding="utf-8")
    result = manager.push(str(git_site), "Deuxième tentative")
    assert result["success"] and "Commits envoyés: 2" in result["message"]
    assert manager.pending(str(git_site))["ahead"] == 0


def test_first_push_of_a_new_branch_sets_upstream(manager, git_site):
    git(git_site, "checkout", "-q", "-b", "brouillon")
    edit(git_site)
    pending = manager.pending(str(git_site))
    assert pending["has_upstream"] is False and pending["ahead"] == 1
    assert manager.push(str(git_site), "Brouillon")["success"]
    assert git(git_site, "rev-parse", "--abbrev-ref", "brouillon@{upstream}") == "origin/brouillon"


def test_published_file(manager, git_site):
    original = (git_site / "index.html").read_bytes().decode("utf-8")
    edit(git_site)
    git(git_site, "commit", "-qam", "Pas encore envoyé")
    assert manager.published_file(str(git_site), "index.html") == (True, original)  # CRLF compris
    assert manager.published_file(str(git_site), "absent.html") == (True, None)
    git(git_site, "checkout", "-q", "-b", "locale")
    assert manager.published_file(str(git_site), "index.html") == (False, None)


def test_pull_and_clone(manager, git_site, tmp_path):
    other = tmp_path / "autre"
    assert manager.clone(str(tmp_path / "remote.git"), str(other))["success"]
    (other / "page" / "nouvelle.html").write_text("<p>nouvelle</p>", encoding="utf-8")
    git(other, "add", "-A")
    git(other, "commit", "-qm", "Depuis un autre poste")
    git(other, "push", "-q")
    assert manager.pull(str(git_site))["success"]
    assert (git_site / "page" / "nouvelle.html").exists()
    assert not manager.clone(str(tmp_path / "absent.git"), str(tmp_path / "x"))["success"]
    assert not manager.pull(str(tmp_path))["success"]


def test_discard(manager, git_site):
    git(git_site, "commit", "--allow-empty", "-qm", "Commit pas encore envoyé")
    edit(git_site)
    (git_site / "nouveau.html").write_text("x", encoding="utf-8")
    result = manager.discard(str(git_site))
    assert result["success"] and result["removed"] == []
    assert b"Offre sp\xc3\xa9ciale" in (git_site / "index.html").read_bytes()
    assert (git_site / "nouveau.html").exists()
    result = manager.discard(str(git_site), remove_untracked=True)
    assert result["removed"] == ["nouveau.html"] and not (git_site / "nouveau.html").exists()
    assert manager.pending(str(git_site))["ahead"] == 1  # Les commits restent


def test_status_report(manager, git_site, tmp_path):
    edit(git_site)
    (git_site / "nouveau.html").write_text("x", encoding="utf-8")
    git(git_site, "add", "nouveau.html")
    (git_site / "brouillon.html").write_text("x", encoding="utf-8")
    output = manager.get_status(str(git_site))["output"]
    for expected in ("Branche actuelle: main", "[AJOUTER] nouveau.html", "[MODIFIER] index.html",
                     "[EN AJOUT] brouillon.html", "Suivi: origin/main", "Site initial"):
        assert expected in output
    assert not manager.get_status(str(tmp_path / "rien"))["success"]
