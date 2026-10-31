#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Éditeur - Liste des pages, chargement des éléments éditables, sauvegarde, extrait de code
"""

import time

from flask import Blueprint, jsonify, request

from api.services import content_hash, error, read_page, services
from content.categories import editable_categories
from content.css_weights import bold_info
from content.published import published_versions
from content.structure import repeatable

bp = Blueprint("editor", __name__)


@bp.get("/api/files")
def list_files():
    return jsonify({"success": True, "files": services().page_files()})


def _published_versions(s, name, elements):
    """Version envoyée sur GitHub de chaque élément (null : absent de cette version), pour les marqueurs +/−/~"""
    if not (s.git_found and s.has_repository()):
        return False
    published_known, published_content = s.git.published_file(str(s.repo_path()), name)
    if published_known:
        content = published_content or ""
        # value : texte, ou src d'une iframe ou d'une image (qui n'est pas dans le contenu)
        published = [{"tag": e["tag"], "html": source["html"], "value": e["editable_value"]} for e, source in
                     zip(s.html.extract_editable_elements(content).get("elements", []),
                         s.html.extract_editable_sources(content))]
        # Associés par leur contenu : un élément ajouté ou supprimé ne décale pas les suivants
        for element, (html, value) in zip(elements, published_versions(elements, published)):
            element["published_html"], element["published_value"] = html, value
    return published_known


@bp.get("/api/files/<path:name>")
def load_file(name):
    s = services()
    file_path = s.resolve_page(name)
    if file_path is None:
        return error(f"Fichier introuvable: {name}", 404)

    content = read_page(file_path)
    start = time.perf_counter()
    result = s.html.extract_editable_elements(content)
    sources = s.html.extract_editable_sources(content)
    bold_flags, bold_selectors = bold_info(s.repo_path(), name, content)
    categories = editable_categories(content)
    repeats = repeatable(content)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if not len(sources) == len(bold_flags) == len(categories) == len(repeats) == len(result["elements"]):
        return error("Structure HTML non reconnue : le nombre d'éléments éditables ne correspond pas", 500)

    # value : texte (ou src d'une iframe, d'une image) ; html : contenu source exact, édité en texte enrichi
    # repeat : "li" ou "tr" si l'élément de liste ou la ligne de tableau peut être dupliqué ou supprimé
    elements = [
        {
            "index": e["index"],
            "id": e["id"],
            "tag": e["tag"],
            "is_iframe": e["is_iframe"],
            "is_image": e["is_image"],
            "value": e["editable_value"],
            "html": source["html"],
            "nested": source["nested"],
            "bold": bold,
            "category": category,
            "repeat": repeat,
        }
        for e, source, bold, category, repeat in zip(result["elements"], sources, bold_flags, categories, repeats)
    ]
    published_known = _published_versions(s, name, elements)

    s.logger.log(f"Fichier ouvert: {name} ({len(elements)} éléments éditables, {elapsed_ms:.0f} ms)")
    # Une page sans élément éditable n'est pas une erreur : le message est affiché à la place de la liste
    return jsonify({
        "success": True,
        "notice": result.get("error"),
        "elements": elements,
        "bold_selectors": bold_selectors,
        "published_known": published_known,
        "hash": content_hash(content),
        "parse_ms": round(elapsed_ms),
    })


@bp.post("/api/files/<path:name>")
def save_file(name):
    s = services()
    file_path = s.resolve_page(name)
    if file_path is None:
        return error(f"Fichier introuvable: {name}", 404)

    data = request.get_json(force=True)
    content = read_page(file_path)

    # Les éléments sont repérés par leur index : refuser si le fichier a changé depuis le chargement
    if data.get("hash") != content_hash(content):
        return error("Le fichier a été modifié depuis son chargement. Rechargez-le avant de sauvegarder.", 409)

    values = {int(k): v for k, v in data.get("values", {}).items()}
    result = s.html.apply_editable_html(content, values)
    if not result["success"]:
        s.logger.log(f"Erreur sauvegarde: {result['error']}")
        return error(f"Impossible de sauvegarder: {result['error']}", 500)

    s.html.write_file(file_path, result["content"])

    # Générer automatiquement le sitemap après la sauvegarde
    sitemap_result = s.update_sitemap()

    return jsonify({
        "success": True,
        "message": f"Fichier sauvegardé: {name} ({result['changed']} élément(s) modifié(s))",
        "sitemap": sitemap_result.get("message") or sitemap_result.get("error"),
        "hash": content_hash(result["content"]),
    })


@bp.post("/api/snippet/<path:name>")
def file_snippet(name):
    """Code source d'un élément tel qu'il serait sauvegardé, sans écrire le fichier"""
    s = services()
    file_path = s.resolve_page(name)
    if file_path is None:
        return error(f"Fichier introuvable: {name}", 404)

    data = request.get_json(force=True)
    content = read_page(file_path)
    if data.get("hash") != content_hash(content):
        return error("Le fichier a été modifié depuis son chargement. Rechargez-le.", 409)

    values = {int(k): v for k, v in data.get("values", {}).items()}
    result = s.html.apply_editable_html(content, values)
    if not result["success"]:
        return error(f"Aperçu du code impossible: {result['error']}", 500)

    snippet = s.html.editable_snippet(result["content"], int(data.get("index", -1)))
    if snippet is None:
        return error("Élément introuvable", 404)
    return jsonify({"success": True, **snippet})
