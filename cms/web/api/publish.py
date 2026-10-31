#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publication - Vérification avant d'envoyer, suivi de la mise en ligne, reprise de la version en ligne
"""

from flask import Blueprint, jsonify, request

from api.services import error, services
from publishing.verification.checks import check_pages
from publishing.verification.online import online_status

bp = Blueprint("publish", __name__)


@bp.get("/api/checks")
def checks():
    """scope=pending : pages pas encore publiées (avant un push) ; scope=all : tout le site"""
    s = services()
    pages = s.page_files() if request.args.get("scope") == "all" else s.git.unpublished_pages(str(s.repo_path()))
    problems = check_pages(s.repo_path(), pages)
    return jsonify({"success": True, "pages": pages, "problems": problems})


@bp.get("/api/online")
def online():
    """Pages envoyées déjà visibles sur le site en ligne (GitHub Pages republie en une à deux minutes)"""
    s = services()
    base_url = s.sitemap.detect_base_url(s.repo_path(), s.config.get_site_url())
    if not base_url:
        return error("URL du site introuvable : renseignez-la dans les paramètres")
    pages = [page for page in request.args.getlist("page") if page in s.page_files()]
    return jsonify({"success": True, "base_url": base_url, **online_status(base_url, s.repo_path(), pages)})


@bp.post("/api/git/reset-to-remote")
def reset_to_remote():
    """Après un conflit : abandonner les modifications et commits locaux, reprendre la version en ligne"""
    s = services()
    result = s.git.reset_to_remote(str(s.repo_path()))
    if not result["success"]:
        return error(result["message"], 500)
    return jsonify(result)
