#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : conflits avec GitHub (quelqu'un d'autre a modifié le site entre-temps)"""

import pytest

from conftest import git
from publishing.git.git_manager import GitManager


@pytest.fixture
def manager(logger):
    return GitManager(logger)


@pytest.fixture
def other(git_site, tmp_path):
    """Un autre poste, avec son propre clone du site"""
    clone = tmp_path / "autre-poste"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    return clone


def replace(folder, page, old, new):
    path = folder / page
    path.write_bytes(path.read_bytes().replace(old.encode("utf-8"), new.encode("utf-8")))


def publish_from(other, page, old, new, message="Depuis un autre poste"):
    replace(other, page, old, new)
    git(other, "commit", "-qam", message)
    git(other, "push", "-q")


def no_operation_in_progress(git_site):
    git_dir = git_site / ".git"
    return not any((git_dir / name).exists() for name in ("MERGE_HEAD", "rebase-merge", "rebase-apply"))


def test_push_after_someone_else_published_elsewhere(manager, git_site, other):
    publish_from(other, "page/formations.html", "Formation moto.", "Formation moto A2.")
    replace(git_site, "index.html", "Offre spéciale", "Offre du mois")
    result = manager.push(str(git_site), "Mon offre")
    assert result["success"] and "récupérées" in result["message"] and result["pages"] == ["index.html"]
    assert git(git_site, "log", "origin/main", "--format=%s", "-2").splitlines() == ["Mon offre", "Depuis un autre poste"]
    assert "Formation moto A2." in (git_site / "page" / "formations.html").read_text(encoding="utf-8")


def test_push_conflict_keeps_everything_and_explains(manager, git_site, other):
    publish_from(other, "index.html", "Offre spéciale", "Offre de l'autre poste")
    replace(git_site, "index.html", "Offre spéciale", "Mon offre")
    result = manager.push(str(git_site), "Mon offre")
    assert result["success"] is False and result["conflict"] is True
    assert "Conflit" in result["message"] and "index.html" in result["message"]
    assert no_operation_in_progress(git_site)
    assert "Mon offre" in (git_site / "index.html").read_text(encoding="utf-8")
    assert manager.pending(str(git_site))["ahead"] == 1  # Mon commit est gardé


def test_pull_conflict_changes_nothing(manager, git_site, other):
    publish_from(other, "index.html", "Offre spéciale", "Offre de l'autre poste")
    replace(git_site, "index.html", "Offre spéciale", "Mon offre")
    git(git_site, "commit", "-qam", "Pas encore publié")
    result = manager.pull(str(git_site))
    assert result["success"] is False and result["conflict"] is True and "Rien n'a été récupéré" in result["message"]
    assert no_operation_in_progress(git_site)
    assert "Mon offre" in (git_site / "index.html").read_text(encoding="utf-8")


def test_pull_with_unsaved_changes_on_the_same_file(manager, git_site, other):
    publish_from(other, "index.html", "Offre spéciale", "Offre de l'autre poste")
    replace(git_site, "index.html", "Bienvenue", "Bonjour")  # Pas commité
    result = manager.pull(str(git_site))
    assert result["success"] is False and "Publiez-les ou annulez-les" in result["message"]
    assert "Bonjour" in (git_site / "index.html").read_text(encoding="utf-8")


def test_reset_to_remote_after_a_conflict(manager, git_site, other):
    publish_from(other, "index.html", "Offre spéciale", "Offre de l'autre poste")
    replace(git_site, "index.html", "Offre spéciale", "Mon offre")
    manager.push(str(git_site), "Mon offre")
    result = manager.reset_to_remote(str(git_site))
    assert result["success"] and "Offre de l'autre poste" in (git_site / "index.html").read_text(encoding="utf-8")
    assert manager.pending(str(git_site))["ahead"] == 0
    git(git_site, "checkout", "-q", "-b", "jamais-publiee")
    assert "jamais été publiée" in manager.reset_to_remote(str(git_site))["message"]


def test_unpublished_pages(manager, git_site):
    replace(git_site, "page/formations.html", "Formation moto.", "Moto.")
    git(git_site, "commit", "-qam", "Pas encore envoyé")
    replace(git_site, "index.html", "Offre spéciale", "Offre")
    (git_site / "page" / "nouvelle.html").write_text("<p>x</p>", encoding="utf-8")
    (git_site / "style" / "style.css").write_text("p {}", encoding="utf-8")  # Pas une page
    assert sorted(manager.unpublished_pages(str(git_site))) == ["index.html", "page/formations.html", "page/nouvelle.html"]
    assert manager.unpublished_pages(str(git_site / "absent")) == []


def test_pull_when_both_sides_have_commits(manager, git_site, other):
    """Corrigé en v2.1.3 : Git refusait (« divergent branches ») avec sa configuration par défaut"""
    publish_from(other, "page/formations.html", "Formation moto.", "Formation moto A2.")
    replace(git_site, "index.html", "Offre spéciale", "Mon offre")
    git(git_site, "commit", "-qam", "Pas encore publié")
    assert manager.pull(str(git_site))["success"]
    assert "Formation moto A2." in (git_site / "page" / "formations.html").read_text(encoding="utf-8")
    assert "Mon offre" in (git_site / "index.html").read_text(encoding="utf-8")
