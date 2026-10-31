#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : branches du site (liste, création, changement, fusion, suppression)"""

import pytest
from git import Repo

from conftest import git
from publishing.git import branches

PAGE = "page/formations.html"


@pytest.fixture
def repo(git_site):
    return Repo(git_site)


def edit_and_commit(site, text, message):
    path = site / PAGE
    path.write_bytes(path.read_bytes().replace(b"</body>", f"<p>{text}</p></body>".encode()))
    git(site, "commit", "-q", "-am", message)


def names(repo):
    return [(b["name"], b["current"], b["published"], b["local"], b["remote"])
            for b in branches.list_branches(repo)["branches"]]


def test_list_and_published_branch(repo, git_site, tmp_path):
    assert branches.list_branches(repo)["published"] == "main"  # Sans origin/HEAD : main
    git(git_site, "push", "-q", "origin", "main:en-ligne-seulement")
    git(git_site, "fetch", "-q")
    git(git_site, "branch", "local-seulement")
    assert names(repo) == [("main", True, True, True, True), ("en-ligne-seulement", False, False, False, True),
                           ("local-seulement", False, False, True, False)]
    # Un clone connaît la branche par défaut de GitHub (origin/HEAD)
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(tmp_path / "remote.git"), str(clone))
    assert branches.default_branch(Repo(clone)) == "main"


def test_create_keeps_unsaved_changes(repo, git_site):
    (git_site / PAGE).write_bytes((git_site / PAGE).read_bytes() + b"<!-- en cours -->")
    result = branches.create(repo, " brouillon ")
    assert result["success"] and repo.active_branch.name == "brouillon"
    assert (git_site / PAGE).read_bytes().endswith(b"<!-- en cours -->")
    with pytest.raises(ValueError, match="existe déjà"):
        branches.create(repo, "main")
    for bad in ("avec espace", "a..b", "", "-x"):
        with pytest.raises(ValueError, match="invalide"):
            branches.create(repo, bad)


def test_switch(repo, git_site):
    branches.create(repo, "brouillon")
    edit_and_commit(git_site, "Brouillon", "Texte du brouillon")
    assert branches.switch(repo, "main")["success"] and b"Brouillon" not in (git_site / PAGE).read_bytes()
    branches.switch(repo, "brouillon")
    assert b"Brouillon" in (git_site / PAGE).read_bytes()
    with pytest.raises(ValueError, match="introuvable"):
        branches.switch(repo, "inconnue")
    (git_site / PAGE).write_bytes(b"modifie")
    with pytest.raises(ValueError, match="changer de branche"):
        branches.switch(repo, "main")  # Modifications non publiées : on reste sur la branche
    assert repo.active_branch.name == "brouillon"


def test_switch_to_a_branch_only_on_github(repo, git_site):
    git(git_site, "push", "-q", "origin", "main:collegue")
    git(git_site, "fetch", "-q")
    branches.switch(repo, "collegue")
    assert repo.active_branch.name == "collegue" and repo.active_branch.tracking_branch().name == "origin/collegue"


def test_merge(repo, git_site):
    branches.create(repo, "brouillon")
    edit_and_commit(git_site, "Nouveau tarif", "Tarifs")
    branches.switch(repo, "main")
    result = branches.merge(repo, "brouillon")
    assert result["success"] and b"Nouveau tarif" in (git_site / PAGE).read_bytes()
    assert len(repo.head.commit.parents) == 2  # Commit de fusion, visible dans l'historique
    assert "déjà" in branches.merge(repo, "brouillon")["message"]
    with pytest.raises(ValueError, match="elle-même"):
        branches.merge(repo, "main")


def test_merge_conflict_changes_nothing(repo, git_site):
    branches.create(repo, "brouillon")
    edit_and_commit(git_site, "Version brouillon", "Brouillon")
    branches.switch(repo, "main")
    edit_and_commit(git_site, "Version main", "Main")
    before = repo.head.commit
    result = branches.merge(repo, "brouillon")
    assert result["conflict"] and PAGE in result["message"]
    assert repo.head.commit == before and not repo.is_dirty(untracked_files=True)
    assert not (git_site / ".git" / "MERGE_HEAD").exists()


def test_delete(repo, git_site):
    branches.create(repo, "brouillon")
    edit_and_commit(git_site, "Jamais fusionné", "Brouillon")
    with pytest.raises(ValueError, match="actuelle"):
        branches.delete(repo, "brouillon")
    with pytest.raises(ValueError, match="publiée"):
        branches.delete(repo, "main")
    branches.switch(repo, "main")
    result = branches.delete(repo, "brouillon")
    assert result["unmerged"] and "brouillon" in [b.name for b in repo.branches]  # Rien de perdu sans confirmation
    assert branches.delete(repo, "brouillon", force=True)["success"]
    assert "brouillon" not in [b.name for b in repo.branches]


def remote_branches(tmp_path):
    return git(tmp_path / "remote.git", "branch", "--format=%(refname:short)").split()


def test_delete_on_github_too(repo, git_site, tmp_path):
    branches.create(repo, "brouillon")
    edit_and_commit(git_site, "Poussé, jamais fusionné", "Brouillon")
    git(git_site, "push", "-q", "-u", "origin", "brouillon")
    branches.switch(repo, "main")
    # Copie gardée sur GitHub : rien n'est perdu en la supprimant d'ici seulement
    assert branches.delete(repo, "brouillon")["success"] and "brouillon" in remote_branches(tmp_path)
    # Seulement sur GitHub : il faut cocher « aussi sur GitHub »
    with pytest.raises(ValueError, match="aussi sur GitHub"):
        branches.delete(repo, "brouillon")
    # La supprimer aussi de GitHub perdrait ses modifications : confirmation demandée
    assert branches.delete(repo, "brouillon", remote=True)["unmerged"] and "brouillon" in remote_branches(tmp_path)
    result = branches.delete(repo, "brouillon", force=True, remote=True)
    assert result["message"].endswith("supprimée de GitHub") and remote_branches(tmp_path) == ["main"]
    assert "brouillon" not in [b["name"] for b in branches.list_branches(repo)["branches"]]


def test_delete_merged_branch_everywhere(repo, git_site, tmp_path):
    branches.create(repo, "fini")
    edit_and_commit(git_site, "Fini", "Fini")
    git(git_site, "push", "-q", "-u", "origin", "fini")
    branches.switch(repo, "main")
    branches.merge(repo, "fini")
    result = branches.delete(repo, "fini", remote=True)  # Fusionnée : pas de confirmation
    assert result["message"].endswith("supprimée de cet ordinateur et de GitHub") and remote_branches(tmp_path) == ["main"]


def test_api(site_client, git_site):
    data = site_client.get("/api/git/branches").get_json()
    assert data["current"] == "main" and data["published"] == "main"
    response = site_client.post("/api/git/branches", json={"action": "create", "name": "brouillon"})
    assert response.status_code == 200 and response.get_json()["current"] == "brouillon"
    assert site_client.post("/api/git/branches", json={"action": "create", "name": "a b"}).status_code == 400
    assert site_client.post("/api/git/branches", json={"action": "reset", "name": "x"}).status_code == 400
    edit_and_commit(git_site, "Brouillon", "Brouillon")
    site_client.post("/api/git/branches", json={"action": "switch", "name": "main"})
    response = site_client.post("/api/git/branches", json={"action": "delete", "name": "brouillon"})
    assert response.status_code == 409 and response.get_json()["unmerged"]
    assert site_client.post("/api/git/branches", json={"action": "delete", "name": "brouillon",
                                                       "force": True}).status_code == 200
    fetched = site_client.get("/api/git/branches?fetch=1").get_json()
    assert fetched["message"].startswith("✓") and [b["name"] for b in fetched["branches"]] == ["main"]


def test_api_without_repository(client):
    assert client.get("/api/git/branches").status_code == 400
