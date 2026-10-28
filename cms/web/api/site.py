#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site - Sitemap et serveur de prévisualisation
"""

import threading
import time

from flask import Blueprint, jsonify, request

from api.services import error, services

bp = Blueprint("site", __name__)


@bp.get("/api/sitemap")
def sitemap_info():
    s = services()
    repo_path = s.repo_path()
    if not repo_path.is_dir():
        return jsonify({"success": True, "location": None, "base_url": ""})
    location = s.sitemap.find_sitemap(repo_path)
    relative = location.relative_to(repo_path).as_posix() if location else "sitemap.xml"
    return jsonify({
        "success": True,
        "location": relative if location else None,
        "base_url": s.sitemap.detect_base_url(repo_path, s.config.get_site_url(), relative),
    })


@bp.post("/api/sitemap")
def sitemap_generate():
    result = services().update_sitemap()
    if not result["success"]:
        return error(result["error"], 500)
    return jsonify({"success": True, "message": result["message"], "base_url": result["base_url"]})


@bp.get("/api/preview")
def preview_status():
    return jsonify(services().preview_status())


@bp.post("/api/preview/start")
def preview_start():
    s = services()
    if s.preview.is_running():
        return jsonify({"success": True, **s.preview_status()})

    try:
        port = int(request.get_json(force=True).get("port"))
    except (TypeError, ValueError):
        return error("Le port doit être un nombre valide")
    if not 1 <= port <= 65535:
        return error(f"Le port doit être entre 1 et 65535 (reçu: {port})")
    if not s.repo_path().exists():
        return error("Le chemin du repository n'existe pas")

    # Script injecté dans les pages ouvertes par l'aperçu en direct de l'éditeur
    preview_script = (s.resources.static_dir / "preview-helper.js").read_text(encoding="utf-8")
    thread = threading.Thread(
        target=s.preview.start,
        args=(str(s.repo_path()), port, s.preview_logs.append, preview_script),
        daemon=True
    )
    thread.start()
    s.preview_port = port

    # Laisser le temps au serveur de démarrer (ou d'échouer, ex: port occupé)
    for _ in range(20):
        if s.preview.is_running() or not thread.is_alive():
            break
        time.sleep(0.05)

    status = s.preview_status()
    if not status["running"]:
        logs = s.preview_logs
        return jsonify({"success": False, "error": logs[-1] if logs else "Échec du démarrage", **status})
    return jsonify({"success": True, **status})


@bp.post("/api/preview/stop")
def preview_stop():
    s = services()
    s.preview.stop()
    s.preview_logs.append("Serveur arrêté")
    return jsonify({"success": True, **s.preview_status()})
