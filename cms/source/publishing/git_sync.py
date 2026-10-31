#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synchronisation avec GitHub - Pull et push, avec les conflits expliqués simplement.

Le repository n'est jamais laissé à moitié fusionné : en cas de conflit, la fusion est annulée
et un message dit quoi faire. Les commits locaux sont toujours conservés.
"""

import datetime

from git import Actor, GitCommandError, PushInfo

# Push refusé parce que GitHub a reçu d'autres commits entre-temps
REJECTED = ("rejected", "fetch first", "non-fast-forward")
CONFLICT_HELP = ("Vos modifications sont gardées sur cet ordinateur, mais pas publiées. Vous pouvez reprendre "
                 "la version en ligne (vos modifications seront perdues) ou demander de l'aide à un développeur.")


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ahead(repo):
    """Commits locaux pas encore envoyés (None si la branche n'a pas de branche distante)"""
    tracking = repo.active_branch.tracking_branch()
    if tracking is None:
        return None
    return int(repo.git.rev_list("--count", f"{tracking.name}..HEAD"))


def _send(origin, refspec, **options):
    """Push qui lève une erreur si une référence est refusée (GitPython ne le fait pas toujours)"""
    infos = origin.push(refspec=refspec, **options)
    # Refus d'abord : Git l'écrit dans la sortie (drapeaux), pas dans le message d'erreur
    for info in infos:
        if info.flags & (PushInfo.REJECTED | PushInfo.REMOTE_REJECTED):
            raise GitCommandError(["git", "push"], 1, f"rejected: {info.summary.strip()}")
    if getattr(infos, "error", None):
        raise infos.error
    for info in infos:
        if info.flags & PushInfo.ERROR:
            raise GitCommandError(["git", "push"], 1, info.summary.strip())


def unmerged(repo):
    return [line for line in repo.git.diff("--name-only", "--diff-filter=U").splitlines() if line]


def pages_to_publish(repo):
    """Pages HTML modifiées dans les commits pas encore envoyés"""
    tracking = repo.active_branch.tracking_branch()
    if not repo.head.is_valid():
        return []
    files = (repo.git.diff("--name-only", f"{tracking.name}..HEAD") if tracking is not None
             else repo.git.ls_files()).splitlines()
    return [f for f in files if f.lower().endswith((".html", ".htm"))]


def pull(repo):
    """Récupérer les modifications de GitHub. Retourne le résultat pour l'interface"""
    origin = repo.remotes.origin
    origin.fetch()
    branch = repo.active_branch.name
    try:
        # Fusion explicite, sans éditeur : sinon Git refuse quand les deux côtés ont des commits
        origin.pull(branch, no_rebase=True, no_edit=True)
    except GitCommandError as error:
        conflicts = unmerged(repo)
        if conflicts:
            repo.git.merge("--abort")
            return {"success": False, "conflict": True, "message": (
                f"✗ Conflit : les mêmes passages ont été modifiés sur GitHub et sur cet ordinateur "
                f"({', '.join(conflicts)}). Rien n'a été récupéré. {CONFLICT_HELP}")}
        if "would be overwritten" in str(error):
            return {"success": False, "message": (
                "✗ Des modifications pas encore publiées touchent les fichiers modifiés sur GitHub. "
                "Publiez-les ou annulez-les, puis récupérez à nouveau.")}
        raise
    return {"success": True, "message": f"✓ Pull réussi\nBranche: {branch}\nTimestamp: {now()}"}


def _rebase_on_remote(repo, tracking):
    """Rejouer les commits locaux après ceux de GitHub. Retourne les fichiers en conflit (rien n'est changé alors)"""
    repo.remotes.origin.fetch()
    try:
        repo.git.rebase(tracking.name)
    except GitCommandError:
        conflicts = unmerged(repo) or ["?"]
        repo.git.rebase("--abort")
        return conflicts
    return []


def push(repo, commit_message, author=None):
    """Commit des modifications (s'il y en a) puis push de tout ce qui n'est pas encore envoyé.
    author : (nom, e-mail) de la personne connectée, auteur du commit (l'identité Git du poste l'envoie)"""
    branch = repo.active_branch
    committed = repo.is_dirty(untracked_files=True)
    if committed:
        repo.git.add(A=True)
        repo.index.commit(commit_message, author=Actor(*author) if author else None)
    waiting = ahead(repo)
    if not committed and waiting == 0:
        return {"success": True, "message": "ℹ️  Aucune modification à pousser", "pages": []}

    pages = pages_to_publish(repo)
    origin = repo.remotes.origin
    merged = ""
    if waiting is None:
        # Première publication de la branche : créer la branche distante et la suivre
        _send(origin, f"{branch.name}:{branch.name}", set_upstream=True)
    else:
        try:
            _send(origin, branch.name)
        except GitCommandError as error:
            if not any(word in str(error) for word in REJECTED):
                raise
            conflicts = _rebase_on_remote(repo, branch.tracking_branch())
            if conflicts:
                return {"success": False, "conflict": True, "message": (
                    f"✗ Conflit : quelqu'un a modifié les mêmes passages sur GitHub depuis votre dernière "
                    f"récupération ({', '.join(conflicts)}). {CONFLICT_HELP}")}
            _send(origin, branch.name)
            merged = "\nLes modifications faites entre-temps sur GitHub ont été récupérées."

    latest = repo.head.commit
    sent = f"\nCommits envoyés: {waiting}" if waiting and waiting > (1 if committed else 0) else ""
    message = (f"✓ Push réussi\nMessage: {latest.message.strip()}\nHash: {latest.hexsha[:7]}\n"
               f"Branche: {branch.name}{sent}{merged}\nTimestamp: {now()}")
    return {"success": True, "message": message, "pages": pages}


def reset_to_remote(repo):
    """Abandonner les modifications et les commits locaux : reprendre exactement la version en ligne"""
    tracking = repo.active_branch.tracking_branch()
    if tracking is None:
        raise ValueError("Cette branche n'a jamais été publiée : il n'y a pas de version en ligne à reprendre")
    repo.remotes.origin.fetch()
    repo.git.reset("--hard", tracking.name)
    return {"success": True, "message": f"✓ Version en ligne reprise ({tracking.name})"}
