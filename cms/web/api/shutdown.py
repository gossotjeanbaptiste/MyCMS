#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quitter - Ce qui reste à faire avant de fermer, puis arrêt du processus (aussi pour installer une mise à jour)
"""

import os
import sys
import tempfile
import threading
from pathlib import Path

from flask import Blueprint, jsonify, session

from api.auth import current_user
from api.services import error, services
from core import updates
from desktop import installer
from desktop.tray import stop_tray
from version import VERSION

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


def _close(s, message):
    """Prévisualisation et session fermées, puis sortie du processus juste après l'envoi de la réponse"""
    if s.preview.is_running():
        s.preview.stop()
    session.clear()
    s.logger.log(message)
    threading.Timer(0.5, _exit_process, args=(s.tray,)).start()


@bp.post("/api/quit")
def quit_app():
    """Arrêter MyCMS : prévisualisation, session, puis le processus une fois la réponse envoyée"""
    _close(services(), "MyCMS fermé depuis l'interface")
    return jsonify({"success": True})


@bp.post("/api/update/install")
def install_update():
    """Télécharger le .msi de la nouvelle version, lancer l'installeur, puis fermer MyCMS, qu'il relance à la fin.
    Réservé aux administrateurs, et à l'application installée (depuis les sources, il n'y a rien à remplacer)"""
    s = services()
    if not s.auth.is_admin(current_user()):
        return error("Réservé aux administrateurs", 403)
    if not getattr(sys, "frozen", False):
        return error("Mise à jour automatique possible seulement depuis l'application installée (.msi)")
    if s.update is None:
        s.update = updates.update_info(VERSION, updates.fetch_latest())
    if not s.update["available"] or not s.update["installer"]:
        return error("Aucune nouvelle version à installer", 409)
    try:
        msi = updates.download(s.update["installer"], Path(tempfile.gettempdir()) / "MyCMS-update")
        installer.launch_installer(msi)
    except (OSError, ValueError) as e:
        s.logger.log(f"Mise à jour impossible : {e}")
        return error(f"Mise à jour impossible : {e}", 502)
    _close(s, f"Installation de MyCMS {s.update['latest']} par {current_user()} : MyCMS se ferme")
    return jsonify({"success": True, "version": s.update["latest"]})
