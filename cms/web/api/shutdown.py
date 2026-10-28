#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quitter - Ce qui reste à faire avant de fermer, puis arrêt du processus
"""

import os
import threading

from flask import Blueprint, jsonify, session

from api.services import services
from desktop.tray import stop_tray

bp = Blueprint("shutdown", __name__)


@bp.get("/api/quit/check")
def quit_check():
    """Ce qui reste à faire avant de quitter : modifications non publiées, prévisualisation active"""
    s = services()
    git = {"available": False, "message": ""}
    if not s.git_found:
        git["message"] = "Git est introuvable : la publication est impossible depuis MyCMS"
    elif not s.has_repository():
        git["message"] = "Le dossier du site n'est pas un repository Git : rien à publier"
    else:
        result = s.git.pending(str(s.repo_path()))
        if result["success"]:
            git = {**result, "available": True}
        else:
            git["message"] = result["message"]
    return jsonify({"success": True, "git": git, "preview_running": s.preview.is_running()})


def _exit_process(tray):
    # Retirer l'icône de notification, sinon elle reste affichée jusqu'au survol de la souris
    stop_tray(tray)
    os._exit(0)


@bp.post("/api/quit")
def quit_app():
    """Arrêter MyCMS : prévisualisation, session, puis le processus une fois la réponse envoyée"""
    s = services()
    if s.preview.is_running():
        s.preview.stop()
    session.clear()
    s.logger.log("MyCMS fermé depuis l'interface")
    # Le serveur de développement Flask n'a pas d'arrêt propre : sortie du processus juste après la réponse
    threading.Timer(0.5, _exit_process, args=(s.tray,)).start()
    return jsonify({"success": True})
