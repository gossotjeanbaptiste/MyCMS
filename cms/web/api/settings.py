#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paramètres et logs - Configuration, choix d'un dossier, journal de l'application
"""

from flask import Blueprint, jsonify, request

from api.services import error, services
from core import updates
from version import VERSION

bp = Blueprint("settings", __name__)


@bp.get("/api/config")
def get_config():
    return jsonify(services().config.get_all_config())


@bp.post("/api/config")
def save_config():
    config = services().config
    data = request.get_json(force=True)
    try:
        if "repo_path" in data:
            config.set_repo_path(data["repo_path"])
        if "site_url" in data:
            config.set_site_url(data["site_url"])
        if "auto_pull" in data:
            config.set_auto_pull(data["auto_pull"])
        if "show_guide" in data:
            config.set_show_guide(data["show_guide"])
        if "default_port" in data:
            config.set_default_port(int(data["default_port"]))
    except (ValueError, TypeError) as e:
        return error(str(e))
    return jsonify({"success": True, "config": config.get_all_config()})


@bp.post("/api/browse-folder")
def browse_folder():
    """Fenêtre « Choisir un dossier » de Windows, ouverte par le serveur local (le navigateur ne donne pas le chemin)"""
    data = request.get_json(force=True, silent=True) or {}
    result = services().folder_picker.choose(str(data.get("title") or "Choisir un dossier"), str(data.get("start") or ""))
    if "error" in result:
        return error(result["error"], 409 if "déjà ouverte" in result["error"] else 500)
    return jsonify({"success": True, **result})


@bp.post("/api/config/reset")
def reset_config():
    config = services().config
    config.reset_to_defaults()
    return jsonify({"success": True, "config": config.get_all_config()})


@bp.get("/api/update")
def update_check():
    """Nouvelle version de MyCMS publiée sur GitHub ? (vérifié une fois par lancement)"""
    s = services()
    if s.update is None:
        s.update = updates.update_info(VERSION, updates.fetch_latest())
    return jsonify(s.update)


@bp.get("/api/logs")
def get_logs():
    return jsonify({"logs": services().logger.get_logs()})


@bp.delete("/api/logs")
def clear_logs():
    services().logger.clear_logs()
    return jsonify({"success": True})
