#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests : détail d'une modification de l'historique (textes changés page par page)"""

import pytest
from git import Repo

from conftest import git
from content.changes import element_changes, word_diff
from publishing.commit_details import commit_details
from publishing.git_manager import GitManager

BEFORE = """<h2>Tarifs</h2><ul><li class="editable">Code : 30 €</li><li class="editable">Livre</li>
<li class="editable">Ancienne ligne</li></ul><p class="editable">Le <b>permis</b></p>"""
AFTER = """<h2>Tarifs</h2><ul><li class="editable">Code : 35 €</li><li class="editable">Livre</li>
<li class="editable">Nouvelle ligne ajoutée ici</li></ul><p class="editable">Le permis</p>"""


def test_word_diff():
    assert word_diff("Le permis coûte 1200 € avec 20 heures.", "Le permis coûte 1350 € avec 20 heures.") == [
        {"op": "equal", "text": "Le permis coûte "}, {"op": "del", "text": "1200 "},
        {"op": "ins", "text": "1350 "}, {"op": "equal", "text": "€ avec 20 heures."}]


def test_element_changes():
    changes, total = element_changes(BEFORE, AFTER)
    kinds = [(c["kind"], c["before"], c["after"]) for c in changes]
    assert ("modified", "Code : 30 €", "Code : 35 €") in kinds
    assert ("formatted", "Le permis", "Le permis") in kinds  # Seul le gras a changé
    assert total == len(changes) and all(c["category"] == "Tarifs" for c in changes)
    replaced = [k for k in kinds if "ligne" in (k[1] + k[2])]
    assert replaced in ([("modified", "Ancienne ligne", "Nouvelle ligne ajoutée ici")],
                        [("added", "", "Nouvelle ligne ajoutée ici"), ("removed", "Ancienne ligne", "")])


def test_new_and_deleted_pages():
    assert [c["kind"] for c in element_changes("", AFTER)[0]] == ["added"] * 4
    assert [c["kind"] for c in element_changes(BEFORE, "")[0]] == ["removed"] * 4
    assert element_changes(BEFORE, BEFORE) == ([], 0)


def test_commit_details(logger, git_site):
    page = git_site / "index.html"
    page.write_bytes(page.read_bytes().replace("Offre spéciale".encode(), "Offre du mois".encode()))
    (git_site / "page" / "nouvelle.html").write_text('<p class="editable">Bonjour</p>', encoding="utf-8")
    (git_site / "style" / "style.css").write_text("p {}", encoding="utf-8")
    GitManager(logger).push(str(git_site), "Offre du mois", ("Marie", "marie@mycms.local"))
    details = commit_details(Repo(git_site), Repo(git_site).head.commit.hexsha[:7])
    assert details["author"] == "Marie" and details["message"] == "Offre du mois"
    assert details["other_files"] == ["style/style.css"]
    index, new = details["pages"]
    assert index["path"] == "index.html" and index["status"] == "modified" and index["total"] == 1
    change = index["changes"][0]
    assert change["kind"] == "modified" and change["before"] == "Offre spéciale" and change["after"] == "Offre du mois"
    assert change["category"] == "Bienvenue à l'auto-école"
    assert "-            <p class=\"highlight editable\"" in index["diff"]
    assert new["path"] == "page/nouvelle.html" and new["status"] == "added" and new["changes"][0]["after"] == "Bonjour"


def test_first_commit_has_no_parent(git_site):
    first = commit_details(Repo(git_site), git(git_site, "rev-list", "--max-parents=0", "HEAD"))
    index = next(p for p in first["pages"] if p["path"] == "index.html")
    assert index["status"] == "added" and index["total"] == 8 and index["diff"].startswith("diff --git")


@pytest.mark.parametrize("ref", ["", "pas-un-hash", "zzzzzzz", "HEAD~1; rm"])
def test_invalid_references(logger, git_site, ref):
    assert GitManager(logger).commit_details(str(git_site), ref) == {"success": False, "message": "Modification introuvable"}


def test_status_no_longer_lists_recent_history(logger, git_site):
    output = GitManager(logger).get_status(str(git_site))["output"]
    assert "Historique récent" not in output and "Dernier commit" in output
