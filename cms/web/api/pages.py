#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pages de l'interface - Page principale et fichiers statiques (JS, CSS)
"""

from flask import Blueprint, render_template, send_file, send_from_directory

from api.services import services

bp = Blueprint("pages", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/favicon.ico")
def favicon():
    """Icône de l'onglet du navigateur : celle de l'exécutable"""
    return send_file(services().resources.icon_file, mimetype="image/x-icon")


@bp.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(services().resources.static_dir, filename)
