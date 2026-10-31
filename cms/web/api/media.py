#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Images - Envoi d'une nouvelle image dans le site (dossier images/) et vignettes de l'éditeur
"""

import os
import posixpath
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from api.services import error, services

bp = Blueprint("media", __name__)

# Pas de SVG : il peut contenir du script
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGES_DIR = "images"


def _inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _free_name(folder, filename):
    """Nom de fichier libre dans folder : photo.png, sinon photo-2.png, photo-3.png…"""
    stem, suffix = os.path.splitext(filename)
    candidate, number = filename, 2
    while (folder / candidate).exists():
        candidate, number = f"{stem}-{number}{suffix}", number + 1
    return candidate


@bp.post("/api/images")
def upload_image():
    """Copier l'image choisie dans images/ ; retourne son adresse relative à la page (pour l'attribut src)"""
    s = services()
    # Avant de lire le formulaire : sinon Flask lirait d'abord tout le fichier
    if request.content_length and request.content_length > MAX_IMAGE_BYTES:
        return error(f"Image trop lourde : {MAX_IMAGE_BYTES // (1024 * 1024)} Mo au plus", 413)
    page = request.form.get("page", "")
    if s.resolve_page(page) is None:
        return error(f"Fichier introuvable: {page}", 404)
    file = request.files.get("file")
    if file is None or not file.filename:
        return error("Aucune image reçue")
    filename = secure_filename(file.filename)
    suffix = os.path.splitext(filename)[1].lower()
    if suffix not in IMAGE_TYPES:
        return error("Format non accepté : PNG, JPG, GIF, WebP ou AVIF")

    folder = s.repo_path() / IMAGES_DIR
    folder.mkdir(exist_ok=True)
    filename = _free_name(folder, filename)
    file.save(folder / filename)
    src = posixpath.relpath(f"{IMAGES_DIR}/{filename}", posixpath.dirname(page) or ".")
    s.logger.log(f"Image ajoutée au site: {IMAGES_DIR}/{filename}")
    return jsonify({"success": True, "src": src, "path": f"{IMAGES_DIR}/{filename}"})


@bp.get("/api/site-image")
def site_image():
    """Image du site, pour la vignette de l'éditeur : src relatif à la page, comme dans le HTML"""
    s = services()
    page = request.args.get("page", "")
    src = request.args.get("src", "").split("?")[0].split("#")[0]
    if s.resolve_page(page) is None or not src or "://" in src or src.startswith("//"):
        return error("Image introuvable", 404)
    root = s.repo_path()
    base = root if src.startswith("/") else (root / page).parent
    path = Path(os.path.normpath(base / src.lstrip("/")))
    if not _inside(path, root) or path.suffix.lower() not in IMAGE_TYPES or not path.is_file():
        return error("Image introuvable", 404)
    return send_file(path)
