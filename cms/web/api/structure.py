#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structure - Dupliquer ou supprimer un élément de liste ou une ligne de tableau depuis l'éditeur
"""

from flask import Blueprint, jsonify, request

from api.services import content_hash, error, read_page, services
from content import structure

bp = Blueprint("structure", __name__)

# Message par type de bloc et par action
MESSAGES = {
    "li": {"duplicate": "Élément de liste dupliqué", "delete": "Élément de liste supprimé"},
    "tr": {"duplicate": "Ligne dupliquée", "delete": "Ligne supprimée"},
}


@bp.post("/api/structure/<path:name>")
def change_structure(name):
    """Le fichier est modifié tout de suite : l'éditeur doit n'avoir rien de non sauvegardé, puis se recharger"""
    s = services()
    file_path = s.resolve_page(name)
    if file_path is None:
        return error(f"Fichier introuvable: {name}", 404)

    data = request.get_json(force=True)
    action = data.get("action")
    if action not in MESSAGES["li"]:
        return error("Action inconnue")
    content = read_page(file_path)
    if data.get("hash") != content_hash(content):
        return error("Le fichier a été modifié depuis son chargement. Rechargez-le.", 409)

    index = int(data.get("index", -1))
    try:
        kind = structure.repeatable(content)[index] if 0 <= index else None
        if action == "duplicate":
            new_content, focus = structure.duplicate(content, index)
        else:
            new_content, focus = structure.remove(content, index), None
    except (ValueError, IndexError) as e:
        return error(str(e) if isinstance(e, ValueError) else "Élément introuvable")

    s.html.write_file(file_path, new_content)
    message = f"{MESSAGES[kind][action]} dans {name}"
    s.logger.log(message)
    sitemap = s.update_sitemap()
    return jsonify({"success": True, "message": message, "hash": content_hash(new_content), "focus": focus,
                    "sitemap": sitemap.get("message") or sitemap.get("error")})
