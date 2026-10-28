#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statut du repository - Rapport lisible affiché dans l'onglet Git
"""

import datetime

from git import Repo


def status_report(repo_path, logger):
    """Récupérer le statut du repository"""
    try:
        repo = Repo(repo_path)
        status = "📊 STATUT DU REPOSITORY\n"
        status += f"{'='*60}\n\n"
        status += f"🌳 Branche actuelle: {repo.active_branch.name}\n"
        try:
            git_status = repo.git.status(porcelain=True).split('\n')
            staged_files = {}
            unstaged_files = {}
            untracked_files = {}
            for line in git_status:
                if not line.strip():
                    continue
                status_code = line[:2]
                file_path = line[3:]
                if status_code[0] in ['A', 'M', 'D', 'R', 'C']:  # Staged
                    staged_files[file_path] = status_code[0]
                if status_code[1] in ['M', 'D']:  # Unstaged
                    unstaged_files[file_path] = status_code[1]
                if status_code == '??':  # Untracked
                    untracked_files[file_path] = 'U'
            if staged_files:
                status += f"\n✅ Changements suivi ({len(staged_files)}):\n"
                for file_path, change_type in staged_files.items():
                    if change_type == 'A':
                        icon = "[AJOUTER]"
                    elif change_type == 'D':
                        icon = "[SUPPRIMER]"
                    elif change_type == 'R':
                        icon = "[RENOMMER]"
                    elif change_type == 'C':
                        icon = "[COPIER]"
                    else:  # Modified
                        icon = "[MODIFIER]"
                    status += f"   {icon} {file_path}\n"
            else:
                status += "\n✓ Aucun changement suivi\n"
            if unstaged_files:
                status += f"\n❌ Fichiers non suivis ({len(unstaged_files)}):\n"
                for file_path, change_type in unstaged_files.items():
                    if change_type == 'D':
                        icon = "[SUPPRIMER]"
                    else:  # Modified
                        icon = "[MODIFIER]"
                    status += f"   {icon} {file_path}\n"
            else:
                status += "\n✓ Aucun fichier non suivi\n"
            if untracked_files:
                status += f"\n📄 À ajouter au repository ({len(untracked_files)}):\n"
                for file_path in list(untracked_files.keys())[:15]:
                    status += f"   [EN AJOUT] {file_path}\n"
                if len(untracked_files) > 15:
                    status += f"   ... et {len(untracked_files) - 15} autres\n"
            else:
                status += "\n✓ Aucun fichier à ajouter\n"
        except Exception as e:
            logger.log(f"Erreur lors du parsing du statut: {e}")
            # Fallback sur l'ancienne méthode
            staged_diffs = repo.index.diff("HEAD")
            if staged_diffs:
                status += f"\n✅ Changements suivi ({len(staged_diffs)}):\n"
                for item in staged_diffs:
                    file_path = item.a_path if item.a_path else item.b_path
                    change_type = item.change_type
                    if change_type == 'A':
                        icon = "[AJOUTER]"
                    elif change_type == 'D':
                        icon = "[SUPPRIMER]"
                    elif change_type == 'R':
                        icon = "[RENOMMER]"
                    else:
                        icon = "[MODIFIER]"
                    status += f"   {icon} {file_path}\n"
            else:
                status += "\n✓ Aucun changement suivi\n"
            unstaged_diffs = repo.index.diff(None)
            if unstaged_diffs:
                status += f"\n❌ Changements non suivi ({len(unstaged_diffs)}):\n"
                for item in unstaged_diffs:
                    file_path = item.a_path
                    change_type = item.change_type
                    if change_type == 'D':
                        icon = "[SUPPRIMER]"
                    else:
                        icon = "[MODIFIER]"
                    status += f"   {icon} {file_path}\n"
            else:
                status += "\n✓ Aucun fichier modifié non suivi\n"
            untracked = repo.untracked_files
            if untracked:
                status += f"\n📄 Fichiers non suivis ({len(untracked)}):\n"
                for file in untracked[:15]:
                    status += f"   [EN AJOUT] {file}\n"
                if len(untracked) > 15:
                    status += f"   ... et {len(untracked) - 15} autres\n"
            else:
                status += "\n✓ Aucun fichier non suivi\n"
        # Dernier commit
        if repo.head.is_valid():
            latest_commit = repo.head.commit
            status += "\n📝 Dernier commit:\n"
            status += f"   Auteur: {latest_commit.author.name}\n"
            status += f"   Message: {latest_commit.message.strip()}\n"
            status += f"   Date: {datetime.datetime.fromtimestamp(latest_commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')}\n"
        # Branche de suivi
        if repo.active_branch.tracking_branch():
            status += f"\n🔗 Suivi: {repo.active_branch.tracking_branch().name}\n"
        # Historique récent
        status += "\n📜 Historique récent:\n"
        for i, commit in enumerate(repo.iter_commits(max_count=5)):
            commit_hash = commit.hexsha[:7]
            status += f"   {i+1}. [{commit_hash}] {commit.message.strip()}\n"
        return {"success": True, "output": status}
    except Exception as e:
        error_msg = f"✗ Erreur lors du statut: {str(e)}"
        return {"success": False, "output": error_msg}
