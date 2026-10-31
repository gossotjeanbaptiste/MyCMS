#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historique lisible - Qui a modifié quelles pages, quand, et si c'est déjà publié
(« Marie a modifié page/tarifs.html le 12 novembre à 14:03 »)
"""

PAGE_SUFFIXES = (".html", ".htm")


def entries(repo, limit=20):
    """Derniers commits de la branche, du plus récent au plus ancien"""
    if not repo.head.is_valid():
        return []
    tracking = repo.active_branch.tracking_branch()
    # Branche jamais publiée : aucun commit n'est en ligne
    unpublished = set(repo.git.rev_list(f"{tracking.name}..HEAD").split()) if tracking is not None else None
    result = []
    for commit in repo.iter_commits(max_count=limit):
        files = sorted(commit.stats.files)
        pages = [f for f in files if str(f).lower().endswith(PAGE_SUFFIXES)]
        result.append({
            "hash": commit.hexsha[:7],
            "author": commit.author.name,
            "date": commit.authored_datetime.isoformat(),
            "message": commit.summary.strip(),  # Première ligne seulement
            "pages": pages,
            "other_files": len(files) - len(pages),
            "published": unpublished is not None and commit.hexsha not in unpublished,
        })
    return result
