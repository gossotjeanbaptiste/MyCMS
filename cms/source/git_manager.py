#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire Git - Opérations de synchronisation avec GitHub
"""

from git import Repo, GitCommandError
from pathlib import Path
import datetime
import os
import subprocess


class GitManager:
    """Gère les opérations Git (pull, push, statut)"""

    def __init__(self, logger):
        self.logger = logger
        self._setup_git_safe_directory()

    def _setup_git_safe_directory(self):
        """Configurer le répertoire comme safe directory pour éviter les erreurs de propriété"""
        try:
            repo_path = Path(__file__).parent.parent.parent
            result = subprocess.run(
                ["git", "config", "--global", "--add",
                    "safe.directory", str(repo_path.resolve())],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.log("Git safe directory configuré")
        except Exception as e:
            self.logger.log(
                f"Attention: impossible de configurer git safe directory: {e}")


class GitManager:
    """Gère les opérations Git (pull, push, statut)"""

    def __init__(self, logger):
        self.logger = logger

    def verify_repo(self, repo_path):
        """Vérifier si le chemin est un repository Git valide"""
        try:
            repo = Repo(repo_path)
            self._ensure_git_config(repo_path)
            return {
                "valid": True,
                "message": f"✓ Repository valide\nBranche: {repo.active_branch.name}\nURL: {repo.remotes.origin.url}"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"✗ Erreur: {str(e)}"
            }

    def _ensure_git_config(self, repo_path):
        """S'assurer que le répertoire est configuré comme safe"""
        try:
            subprocess.run(
                ["git", "config", "--global", "--add",
                    "safe.directory", str(Path(repo_path).resolve())],
                capture_output=True,
                cwd=repo_path
            )
        except:
            pass

    def pull(self, repo_path):
        """Pull les dernières modifications"""
        try:
            self._ensure_git_config(repo_path)
            repo = Repo(repo_path)
            origin = repo.remotes.origin  # Fetch
            origin.fetch()
            current_branch = repo.active_branch  # Pull
            origin.pull(current_branch.name)
            message = f"✓ Pull réussi\nBranche: {current_branch.name}\nTimestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.logger.log(f"Git pull réussi depuis {current_branch.name}")
            return {"success": True, "message": message}
        except GitCommandError as e:
            error_msg = f"✗ Erreur Git: {str(e)}"
            self.logger.log(f"Erreur Git: {error_msg}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"✗ Erreur: {str(e)}"
            self.logger.log(f"Erreur: {error_msg}")
            return {"success": False, "message": error_msg}

    def push(self, repo_path, commit_message):
        """Push les modifications vers le repository distant"""
        try:
            self._ensure_git_config(repo_path)
            repo = Repo(repo_path)
            if repo.is_dirty(untracked_files=True):
                repo.git.add(A=True)
                repo.index.commit(commit_message)  # Commit
                origin = repo.remotes.origin  # Push
                current_branch = repo.active_branch
                origin.push(current_branch.name)
                # Récupérer le hash du dernier commit
                latest_commit = repo.head.commit
                commit_hash = latest_commit.hexsha[:7]
                message = f"✓ Push réussi\nMessage: {commit_message}\nHash: {commit_hash}\nBranche: {current_branch.name}\nTimestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.logger.log(
                    f"Git push réussi: {commit_message} ({commit_hash})")
                return {"success": True, "message": message}
            else:
                message = "ℹ️  Aucune modification à pousser"
                self.logger.log(message)
                return {"success": True, "message": message}
        except GitCommandError as e:
            error_msg = f"✗ Erreur Git: {str(e)}"
            self.logger.log(f"Erreur Git: {error_msg}")
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"✗ Erreur: {str(e)}"
            self.logger.log(f"Erreur: {error_msg}")
            return {"success": False, "message": error_msg}

    def get_status(self, repo_path):
        """Récupérer le statut du repository"""
        try:
            repo = Repo(repo_path)
            status = f"📊 STATUT DU REPOSITORY\n"
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
                    status += f"\n✓ Aucun changement suivi\n"
                if unstaged_files:
                    status += f"\n❌ Fichiers non suivis ({len(unstaged_files)}):\n"
                    for file_path, change_type in unstaged_files.items():
                        if change_type == 'D':
                            icon = "[SUPPRIMER]"
                        else:  # Modified
                            icon = "[MODIFIER]"
                        status += f"   {icon} {file_path}\n"
                else:
                    status += f"\n✓ Aucun fichier non suivi\n"
                if untracked_files:
                    status += f"\n📄 À ajouter au repository ({len(untracked_files)}):\n"
                    for file_path in list(untracked_files.keys())[:15]:
                        status += f"   [EN AJOUT] {file_path}\n"
                    if len(untracked_files) > 15:
                        status += f"   ... et {len(untracked_files) - 15} autres\n"
                else:
                    status += f"\n✓ Aucun fichier à ajouter\n"
            except Exception as e:
                self.logger.log(f"Erreur lors du parsing du statut: {e}")
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
                    status += f"\n✓ Aucun changement suivi\n"
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
                    status += f"\n✓ Aucun fichier modifié non suivi\n"
                untracked = repo.untracked_files
                if untracked:
                    status += f"\n📄 Fichiers non suivis ({len(untracked)}):\n"
                    for file in untracked[:15]:
                        status += f"   [EN AJOUT] {file}\n"
                    if len(untracked) > 15:
                        status += f"   ... et {len(untracked) - 15} autres\n"
                else:
                    status += f"\n✓ Aucun fichier non suivi\n"
            # Dernier commit
            if repo.head.is_valid():
                latest_commit = repo.head.commit
                status += f"\n📝 Dernier commit:\n"
                status += f"   Auteur: {latest_commit.author.name}\n"
                status += f"   Message: {latest_commit.message.strip()}\n"
                status += f"   Date: {datetime.datetime.fromtimestamp(latest_commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')}\n"
            # Branche de suivi
            if repo.active_branch.tracking_branch():
                status += f"\n🔗 Suivi: {repo.active_branch.tracking_branch().name}\n"
            # Historique récent
            status += f"\n📜 Historique récent:\n"
            for i, commit in enumerate(repo.iter_commits(max_count=5)):
                commit_hash = commit.hexsha[:7]
                status += f"   {i+1}. [{commit_hash}] {commit.message.strip()}\n"
            return {"success": True, "output": status}
        except Exception as e:
            error_msg = f"✗ Erreur lors du statut: {str(e)}"
            return {"success": False, "output": error_msg}
