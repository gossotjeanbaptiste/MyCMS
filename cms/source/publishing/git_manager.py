#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire Git - Opérations de synchronisation avec GitHub
"""

import subprocess
from pathlib import Path

from git import GitCommandError, Repo

from publishing import git_sync
from publishing.git_status import status_report


class GitManager:
    """Gère les opérations Git (pull, push, statut)"""

    def __init__(self, logger):
        self.logger = logger

    def _failure(self, error):
        """Échec d'une opération : message pour l'interface, ajouté au journal"""
        prefix = "Erreur Git" if isinstance(error, GitCommandError) else "Erreur"
        error_msg = f"✗ {prefix}: {str(error)}"
        self.logger.log(f"{prefix}: {error_msg}")
        return {"success": False, "message": error_msg}

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

    def clone(self, url, repo_path):
        """Récupérer un repository distant dans un nouveau dossier"""
        try:
            repo = Repo.clone_from(url, repo_path)
            self._ensure_git_config(repo_path)
            message = f"✓ Site récupéré\nDossier: {repo_path}\nBranche: {repo.active_branch.name}"
            self.logger.log(f"Git clone réussi: {url} -> {repo_path}")
            return {"success": True, "message": message}
        except Exception as e:
            return self._failure(e)

    def _sync(self, repo_path, operation, *args):
        """Pull, push ou reprise de la version en ligne (publishing/git_sync), avec le journal"""
        try:
            self._ensure_git_config(repo_path)
            result = operation(Repo(repo_path), *args)
            self.logger.log(result["message"].splitlines()[0])
            return result
        except Exception as e:
            return self._failure(e)

    def pull(self, repo_path):
        """Récupérer les modifications de GitHub (conflit : rien n'est changé, et c'est expliqué)"""
        return self._sync(repo_path, git_sync.pull)

    def push(self, repo_path, commit_message):
        """Commit des modifications (s'il y en a) puis push de tout ce qui n'est pas encore envoyé.
        GitHub a reçu d'autres commits entre-temps : ils sont récupérés, puis l'envoi est refait."""
        return self._sync(repo_path, git_sync.push, commit_message)

    def reset_to_remote(self, repo_path):
        """Abandonner les modifications et commits locaux : reprendre la version en ligne"""
        return self._sync(repo_path, git_sync.reset_to_remote)

    def pending(self, repo_path):
        """Ce qui n'est pas encore publié : fichiers modifiés et commits pas encore envoyés.
        Sans accès réseau : comparé au dernier état connu de la branche distante."""
        try:
            repo = Repo(repo_path)
            files = []
            for line in repo.git.status(porcelain=True).splitlines():
                if line.strip():
                    files.append({"state": line[:2].strip(), "path": line[3:].strip('"')})
            ahead = git_sync.ahead(repo) if repo.head.is_valid() else 0
            return {
                "success": True,
                "branch": repo.active_branch.name,
                "files": files,
                # Branche jamais envoyée : tous ses commits sont à publier
                "ahead": ahead if ahead is not None else sum(1 for _ in repo.iter_commits()),
                "has_upstream": ahead is not None,
            }
        except Exception as e:
            return {"success": False, "message": f"✗ Erreur: {str(e)}"}

    def unpublished_pages(self, repo_path):
        """Pages HTML pas encore publiées : modifiées, nouvelles, ou dans des commits pas encore envoyés"""
        try:
            repo = Repo(repo_path)
            pages = git_sync.pages_to_publish(repo)
            for line in repo.git.status("--porcelain", "--untracked-files=all").splitlines():
                path = line[3:].strip('"')
                if path.lower().endswith((".html", ".htm")) and not line.startswith(" D") and path not in pages:
                    pages.append(path)
            return [page for page in pages if (Path(repo_path) / page).is_file()]
        except Exception:
            return []

    def published_file(self, repo_path, relative_path):
        """Contenu d'un fichier dans la version envoyée sur GitHub (dernier état connu de la branche distante).
        (False, None) : version publiée inconnue (pas de branche distante) ; (True, None) : fichier absent de cette version."""
        try:
            repo = Repo(repo_path)
            tracking = repo.active_branch.tracking_branch()
            if tracking is None:
                return False, None
            try:
                return True, repo.git.show(f"{tracking.name}:{relative_path}", strip_newline_in_stdout=False)
            except GitCommandError:
                return True, None
        except Exception:
            return False, None

    def discard(self, repo_path, remove_untracked=False):
        """Revenir au dernier commit : fichiers suivis restaurés ; fichiers nouveaux supprimés seulement si demandé.
        Les commits pas encore envoyés sont conservés."""
        try:
            repo = Repo(repo_path)
            repo.git.reset("--hard", "HEAD")
            removed = []
            if remove_untracked:
                output = repo.git.clean("-fd")
                removed = [line.removeprefix("Removing ").strip() for line in output.splitlines() if line.strip()]
            message = "✓ Modifications annulées : retour au dernier commit"
            if removed:
                message += f" ({len(removed)} nouveau(x) fichier(s) supprimé(s))"
            self.logger.log(message)
            return {"success": True, "message": message, "removed": removed}
        except Exception as e:
            return self._failure(e)

    def get_status(self, repo_path):
        """Récupérer le statut du repository"""
        return status_report(repo_path, self.logger)
