#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification avant publication - Ce qui casserait la page en ligne :
liens et images vers des fichiers absents du site, ancres introuvables, adresses e-mail ou numéros
de téléphone mal écrits, éléments éditables vidés.
"""

import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from content.html_tree import SRC_TAGS, parse

# Attributs qui pointent vers un fichier du site
LINK_ATTRIBUTES = {"a": "href", "link": "href", "img": "src", "script": "src", "iframe": "src", "source": "src"}
EXTERNAL = re.compile(r"(?i)^([a-z][a-z0-9+.-]*:|//)")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE = re.compile(r"^\+?[\d\s.()-]{6,}$")
TAGS = re.compile(r"<[^>]*>")


def _walk(node):
    for child in node.children:
        if child.kind == "element":
            yield child
            yield from _walk(child)


def _problem(page, content, node, message):
    return {"page": page, "line": content.count("\n", 0, node.start) + 1, "message": message}


def _local_target(repo_path, page, url):
    """Fichier du site visé par une adresse locale, résolue comme le fait le navigateur
    (on ne remonte jamais au-dessus de la racine du site : ../images depuis index.html vise /images)"""
    path = unquote(urlsplit(urljoin(f"http://site/{page}", url)).path)
    target = Path(repo_path) / path.lstrip("/")
    return target / "index.html" if path.endswith("/") or target.is_dir() else target


def _check_link(repo_path, page, url, ids):
    """Message d'erreur pour une adresse, ou None si elle est bonne (ou externe : non vérifiée)"""
    url = url.strip()
    if not url or url.lower().startswith(("javascript:", "data:")):
        return None
    if url.lower().startswith("mailto:"):
        address = unquote(url[7:].split("?")[0])
        return None if all(EMAIL.match(a.strip()) for a in address.split(",")) else f"Adresse e-mail incorrecte : {url}"
    if url.lower().startswith("tel:"):
        return None if PHONE.match(unquote(url[4:])) else f"Numéro de téléphone incorrect : {url}"
    if EXTERNAL.match(url):
        return None
    if url.startswith("#"):
        anchor = unquote(url[1:])
        return None if not anchor or anchor == "top" or anchor in ids else f"Ancre introuvable dans la page : {url}"
    return None if _local_target(repo_path, page, url).is_file() else f"Fichier introuvable : {url}"


def check_page(repo_path, page, content):
    """Problèmes d'une page : [{page, line, message}]"""
    root, editables = parse(content)
    nodes = list(_walk(root))
    ids = {node.attr("id") for node in nodes if node.attr("id")}
    problems = []
    for node in nodes:
        attribute = LINK_ATTRIBUTES.get(node.tag)
        if attribute and node.attr(attribute) is not None:
            message = _check_link(repo_path, page, node.attr(attribute), ids)
            if message:
                problems.append(_problem(page, content, node, message))
    for node in editables:
        if node.tag in SRC_TAGS:
            if not (node.attr("src") or "").strip():
                problems.append(_problem(page, content, node, f"Adresse vide (élément [{node.editable_index}])"))
            continue
        inner = content[node.inner_start:node.inner_end]
        if node.tag not in ("br", "hr") and not TAGS.sub("", inner).replace("&nbsp;", "").strip() \
                and "<img" not in inner.lower():
            problems.append(_problem(page, content, node, f"Élément vide (élément [{node.editable_index}])"))
    return sorted(problems, key=lambda p: p["line"])


def check_pages(repo_path, pages):
    """Problèmes de plusieurs pages (pages illisibles ou absentes ignorées)"""
    problems = []
    for page in pages:
        try:
            with open(Path(repo_path) / page, encoding="utf-8", newline="") as f:
                problems.extend(check_page(repo_path, page, f.read()))
        except (OSError, UnicodeDecodeError):
            continue
    return problems
