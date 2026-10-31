#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statut du repository - Rapport lisible affiché dans l'onglet Git
"""

import datetime

from git import Repo

# Lettre de git status -> libellé affiché
STAGED = {"A": "[AJOUTER]", "D": "[SUPPRIMER]", "R": "[RENOMMER]", "C": "[COPIER]", "M": "[MODIFIER]"}
UNSTAGED = {"D": "[SUPPRIMER]", "M": "[MODIFIER]"}
MAX_UNTRACKED = 15


def _changes(repo):
    """(suivis, non suivis, à ajouter) d'après git status --porcelain"""
    staged, unstaged, untracked = {}, {}, []
    for line in repo.git.status(porcelain=True).split("\n"):
        if not line.strip():
            continue
        code, path = line[:2], line[3:]
        if code == "??":
            untracked.append(path)
            continue
        if code[0] in STAGED:
            staged[path] = STAGED[code[0]]
        if code[1] in UNSTAGED:
            unstaged[path] = UNSTAGED[code[1]]
    return staged, unstaged, untracked


def _section(title, empty, items):
    if not items:
        return f"\n✓ {empty}\n"
    return f"\n{title} ({len(items)}):\n" + "".join(f"   {label} {path}\n" for path, label in items)


def status_report(repo_path, logger):
    """Récupérer le statut du repository"""
    try:
        repo = Repo(repo_path)
        status = "📊 STATUT DU REPOSITORY\n"
        status += f"{'=' * 60}\n\n"
        status += f"🌳 Branche actuelle: {repo.active_branch.name}\n"

        staged, unstaged, untracked = _changes(repo)
        status += _section("✅ Changements suivi", "Aucun changement suivi", staged.items())
        status += _section("❌ Fichiers non suivis", "Aucun fichier non suivi", unstaged.items())
        shown = [(path, "[EN AJOUT]") for path in untracked[:MAX_UNTRACKED]]
        status += _section("📄 À ajouter au repository", "Aucun fichier à ajouter", shown).replace(
            f"({len(shown)})", f"({len(untracked)})", 1)
        if len(untracked) > MAX_UNTRACKED:
            status += f"   ... et {len(untracked) - MAX_UNTRACKED} autres\n"

        if repo.head.is_valid():
            latest = repo.head.commit
            status += "\n📝 Dernier commit:\n"
            status += f"   Auteur: {latest.author.name}\n"
            status += f"   Message: {latest.message.strip()}\n"
            status += f"   Date: {datetime.datetime.fromtimestamp(latest.committed_date).strftime('%Y-%m-%d %H:%M:%S')}\n"

        tracking = repo.active_branch.tracking_branch()
        if tracking:
            status += f"\n🔗 Suivi: {tracking.name}\n"
        # L'historique a sa propre carte dans l'onglet Git (publishing/git/history.py)
        return {"success": True, "output": status}
    except Exception as e:
        logger.log(f"Erreur lors du statut: {e}")
        return {"success": False, "output": f"✗ Erreur lors du statut: {str(e)}"}
