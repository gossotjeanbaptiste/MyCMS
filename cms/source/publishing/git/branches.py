#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Branches du site - Liste, création, changement, fusion et suppression.

Une branche est une copie de travail du site : on peut préparer des modifications sur une branche
« brouillon » sans toucher au site en ligne, puis la fusionner dans la branche publiée (celle que GitHub
Pages met en ligne, la branche par défaut du repository). Comme pour le pull, rien n'est jamais laissé
à moitié fusionné, et on ne change pas de branche avec des modifications pas encore publiées.
"""

from git import GitCommandError

from publishing.git.git_sync import unmerged

PENDING = ("Des modifications ne sont pas encore enregistrées dans un commit : publiez-les ou annulez-les "
           "avant de {}.")


def default_branch(repo):
    """Branche publiée : la branche par défaut de GitHub (origin/HEAD), sinon main ou master s'ils existent"""
    try:
        return repo.git.symbolic_ref("--short", "refs/remotes/origin/HEAD").removeprefix("origin/")
    except GitCommandError:
        names = {b.name for b in repo.branches} | {r.remote_head for r in _remote_branches(repo)}
        return next((name for name in ("main", "master") if name in names), None)


def _remote_branches(repo):
    if "origin" not in [remote.name for remote in repo.remotes]:
        return []
    return [ref for ref in repo.remotes.origin.refs if ref.remote_head != "HEAD"]


def list_branches(repo):
    """Branches de cet ordinateur et de GitHub (dernier état connu, sans réseau), la branche actuelle en premier"""
    current = repo.active_branch.name
    local = {branch.name for branch in repo.branches}
    remote = {ref.remote_head for ref in _remote_branches(repo)}
    published = default_branch(repo)
    branches = [{"name": name, "current": name == current, "published": name == published,
                 "local": name in local, "remote": name in remote}
                for name in sorted(local | remote, key=lambda n: (n != current, n != published, n.lower()))]
    return {"current": current, "published": published, "branches": branches}


def check_name(repo, name):
    """Nom de branche valide pour Git (pas d'espace, pas de « .. »…) ; ValueError sinon"""
    name = str(name or "").strip()
    try:
        repo.git.check_ref_format("--branch", name)
    except GitCommandError:
        raise ValueError(f"Nom de branche invalide : « {name} ». Utilisez des lettres, des chiffres et des tirets, "
                         "sans espace (exemple : brouillon-tarifs).") from None
    return name


def _require_clean(repo, action):
    if repo.is_dirty(untracked_files=True):
        raise ValueError(PENDING.format(action))


def create(repo, name):
    """Nouvelle branche à partir de la branche actuelle, qui devient la branche actuelle.
    Elle n'existe que sur cet ordinateur jusqu'au premier push"""
    name = check_name(repo, name)
    if any(branch["name"] == name for branch in list_branches(repo)["branches"]):
        raise ValueError(f"La branche « {name} » existe déjà")
    source = repo.active_branch.name
    repo.git.checkout("-b", name)  # Les modifications non publiées suivent : rien n'est perdu
    return {"success": True, "message": f"✓ Branche « {name} » créée à partir de « {source} »"}


def switch(repo, name):
    """Passer sur une autre branche ; une branche qui n'est que sur GitHub est récupérée"""
    _require_clean(repo, "changer de branche")
    branches = {b["name"]: b for b in list_branches(repo)["branches"]}
    if name not in branches:
        raise ValueError(f"La branche « {name} » est introuvable")
    if branches[name]["local"]:
        repo.git.checkout(name)
    else:
        repo.git.checkout("-b", name, "--track", f"origin/{name}")
    return {"success": True, "message": f"✓ Vous êtes sur la branche « {name} »"}


def merge(repo, name):
    """Fusionner une branche dans la branche actuelle (commit de fusion). En cas de conflit, rien n'est changé"""
    _require_clean(repo, "fusionner une branche")
    current = repo.active_branch.name
    if name == current:
        raise ValueError("Une branche ne peut pas être fusionnée dans elle-même")
    branches = {b["name"]: b for b in list_branches(repo)["branches"]}
    if name not in branches:
        raise ValueError(f"La branche « {name} » est introuvable")
    source = name if branches[name]["local"] else f"origin/{name}"
    if repo.is_ancestor(repo.commit(source), repo.head.commit):
        return {"success": True, "message": f"ℹ️  « {current} » contient déjà toutes les modifications de « {name} »"}
    try:
        repo.git.merge(source, "--no-ff", "--no-edit")
    except GitCommandError:
        conflicts = unmerged(repo) or ["?"]
        repo.git.merge("--abort")
        return {"success": False, "conflict": True, "message": (
            f"✗ Conflit : les mêmes passages ont été modifiés sur « {name} » et sur « {current} » "
            f"({', '.join(conflicts)}). Rien n'a été fusionné. Demandez de l'aide à un développeur.")}
    return {"success": True, "message": (f"✓ « {name} » fusionnée dans « {current} ». "
                                         "Faites un push pour l'envoyer sur GitHub.")}


def delete(repo, name, force=False):
    """Supprimer une branche de cet ordinateur (pas la branche actuelle ni la branche publiée).
    Sans force, refusé si ses modifications n'ont pas été fusionnées : elles seraient perdues"""
    listing = list_branches(repo)
    if name == listing["current"]:
        raise ValueError("Impossible de supprimer la branche actuelle : passez d'abord sur une autre branche")
    if name == listing["published"]:
        raise ValueError("Impossible de supprimer la branche publiée")
    if name not in {b.name for b in repo.branches}:
        raise ValueError(f"La branche « {name} » n'est pas sur cet ordinateur")
    try:
        repo.git.branch("-D" if force else "-d", name)
    except GitCommandError as error:
        if "not fully merged" in str(error):
            return {"success": False, "unmerged": True, "message": (
                f"La branche « {name} » contient des modifications qui n'ont été fusionnées nulle part : "
                "elles seront perdues.")}
        raise
    return {"success": True, "message": f"✓ Branche « {name} » supprimée de cet ordinateur"}
