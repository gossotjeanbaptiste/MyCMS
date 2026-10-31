#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Branches du site - Liste, création, changement, fusion, suppression (publishing/git/branches)
"""

from flask import Blueprint, jsonify, request
from git import GitCommandError, Repo

from api.auth import current_user
from api.services import error, services
from publishing.git import branches

bp = Blueprint("branches", __name__)

ACTIONS = {"create": branches.create, "switch": branches.switch, "merge": branches.merge}


def _repo():
    s = services()
    if not s.has_repository():
        raise ValueError("Le dossier du site n'est pas un repository Git")
    s.git._ensure_git_config(str(s.repo_path()))
    return Repo(str(s.repo_path()))


@bp.get("/api/git/branches")
def list_branches():
    """Branches connues ; fetch=1 : demander d'abord à GitHub ses branches (réseau)"""
    try:
        repo = _repo()
        message = ""
        if request.args.get("fetch") and "origin" in [remote.name for remote in repo.remotes]:
            try:
                repo.remotes.origin.fetch(prune=True)
                message = "✓ Branches de GitHub récupérées"
            except GitCommandError as e:
                message = f"✗ GitHub injoignable : liste de la dernière récupération ({e.stderr.strip()})"
        return jsonify({"success": True, "message": message, **branches.list_branches(repo)})
    except (ValueError, TypeError) as e:
        # TypeError : HEAD détaché (pas de branche actuelle)
        return error(str(e) if isinstance(e, ValueError) else "Aucune branche active (HEAD détaché)")


@bp.post("/api/git/branches")
def branch_action():
    """action : create, switch, merge ou delete (remote : aussi sur GitHub ; force : même si elle n'a pas
    été fusionnée)"""
    s = services()
    data = request.get_json(force=True, silent=True) or {}
    action, name = data.get("action"), str(data.get("name") or "").strip()
    if action not in ACTIONS and action != "delete":
        return error("Action inconnue")
    if not name:
        return error("Veuillez indiquer le nom de la branche")
    try:
        repo = _repo()
        if action == "delete":
            result = branches.delete(repo, name, bool(data.get("force")), bool(data.get("remote")))
        else:
            result = ACTIONS[action](repo, name)
    except ValueError as e:
        return error(str(e))
    except GitCommandError as e:
        s.logger.log(f"Erreur Git ({action} {name}) : {e}")
        return error(f"✗ Erreur Git : {e.stderr.strip() or e}", 500)
    s.logger.log(f"{result['message'].splitlines()[0]} ({current_user()})")
    if not result["success"]:
        return jsonify(result), 409
    return jsonify({**result, **branches.list_branches(repo)})
