#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Détail d'une modification de l'historique : pour chaque page, les textes modifiés, ajoutés ou supprimés ;
les autres fichiers ; et le code modifié (diff Git), pour un développeur.
"""

import re

from git import GitCommandError

from content.versions.changes import element_changes

HASH_RE = re.compile(r"[0-9a-fA-F]{4,40}")
PAGE_SUFFIXES = (".html", ".htm")
MAX_DIFF_LINES = 300


def _file_at(repo, commit, path):
    """Contenu d'un fichier dans une version (vide s'il n'y existe pas), fins de ligne d'origine"""
    if commit is None:
        return ""
    try:
        return repo.git.show(f"{commit.hexsha}:{path}", strip_newline_in_stdout=False)
    except GitCommandError:
        return ""


def _code_diff(repo, parent, commit, path):
    """Diff Git du fichier, raccourci s'il est trop long"""
    try:
        if parent is None:
            lines = repo.git.show(commit.hexsha, "--format=", "--", path).splitlines()
        else:
            lines = repo.git.diff(parent.hexsha, commit.hexsha, "--", path).splitlines()
    except GitCommandError:
        return ""
    if len(lines) > MAX_DIFF_LINES:
        lines = lines[:MAX_DIFF_LINES] + [f"… ({len(lines) - MAX_DIFF_LINES} lignes de plus)"]
    return "\n".join(lines)


def commit_details(repo, ref):
    """{hash, author, date, message, pages: [{path, status, changes, total, diff}], other_files}"""
    if not HASH_RE.fullmatch(str(ref or "")):
        raise ValueError("Modification introuvable")
    commit = repo.commit(ref)
    parent = commit.parents[0] if commit.parents else None
    pages, others = [], []
    for path in sorted(commit.stats.files):
        if not str(path).lower().endswith(PAGE_SUFFIXES):
            others.append(path)
            continue
        before, after = _file_at(repo, parent, path), _file_at(repo, commit, path)
        changes, total = element_changes(before, after)
        status = "added" if not before else "removed" if not after else "modified"
        pages.append({"path": path, "status": status, "changes": changes, "total": total,
                      "diff": _code_diff(repo, parent, commit, path)})
    return {
        "hash": commit.hexsha[:7],
        "author": commit.author.name,
        "date": commit.authored_datetime.isoformat(),
        "message": commit.message.strip(),
        "pages": pages,
        "other_files": others,
    }
