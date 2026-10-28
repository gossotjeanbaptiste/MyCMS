#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pages de l'interface - Page principale et fichiers statiques (JS, CSS)
"""

from flask import Blueprint, render_template, send_from_directory

from api.services import services

bp = Blueprint("pages", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(services().resources.static_dir, filename)
