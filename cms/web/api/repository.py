#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository Git - Vérification, clone, pull, push, statut, annulation des modifications
"""

import re
import subprocess
from pathlib import Path

from flask import Blueprint, jsonify, request

from api.services import error, services

bp = Blueprint("repository", __name__)


@bp.post("/api/git/verify")
def git_verify():
    s = services()
    result = s.git.verify_repo(str(s.repo_path()))
    return jsonify({"success": result["valid"], "message": result["message"]})


@bp.post("/api/git/clone")
def git_clone():
    """Récupérer le site depuis GitHub ; le dossier cloné devient le repository courant"""
    s = services()
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    if not url:
        return error("Veuillez entrer l'adresse du repository")
    destination = (data.get("path") or "").strip()
    if destination:
        path = Path(destination).expanduser()
    else:
        # Par défaut : dossier personnel / nom du repository (adresse web, SSH ou chemin Windows)
        name = re.split(r"[/\\:]", url.rstrip("/\\"))[-1].removesuffix(".git")
        path = Path.home() / (name or "site")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        return error(f"Le dossier existe déjà et n'est pas vide: {path}")

    result = s.git.clone(url, str(path))
    if not result["success"]:
        return error(result["message"], 500)
    s.config.set_repo_path(str(path))
    return jsonify({**result, "path": str(path)})


@bp.post("/api/git/pull")
def git_pull():
    s = services()
    return jsonify(s.git.pull(str(s.repo_path())))


@bp.post("/api/git/push")
def git_push():
    s = services()
    message = (request.get_json(force=True).get("message") or "").strip()
    if not message:
        return error("Veuillez entrer un message de commit")
    return jsonify(s.git.push(str(s.repo_path()), message))


@bp.get("/api/git/status")
def git_status():
    s = services()
    # has_git : le dossier choisi est un repository (sinon l'interface propose de récupérer le site)
    return jsonify({**s.git.get_status(str(s.repo_path())), "has_git": s.has_repository()})


@bp.post("/api/git/discard")
def git_discard():
    """Revenir au dernier commit (les fichiers nouveaux ne sont supprimés que si demandé)"""
    s = services()
    remove_untracked = bool(request.get_json(force=True).get("remove_untracked"))
    result = s.git.discard(str(s.repo_path()), remove_untracked)
    if not result["success"]:
        return error(result["message"], 500)
    return jsonify(result)


@bp.post("/api/git/add")
def git_add_untracked():
    """Ajouter tous les fichiers non suivis"""
    s = services()
    try:
        result = subprocess.run(
            ["git", "add", "."],
            cwd=str(s.repo_path()),
            capture_output=True,
            text=True,
            timeout=30
        )
    except Exception as e:
        s.logger.log(f"Erreur: {e}")
        return error(str(e), 500)

    if result.returncode == 0:
        s.logger.log("Fichiers non suivis ajoutés avec succès")
        return jsonify({"success": True, "message": "Tous les fichiers non suivis ont été ajoutés"})
    s.logger.log(f"Erreur ajout: {result.stderr}")
    return error(f"Erreur lors de l'ajout: {result.stderr}", 500)
