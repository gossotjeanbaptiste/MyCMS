#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catégories des éléments éditables - Déduites de la structure de la page, pour filtrer l'éditeur.

Pour chaque élément, dans cet ordre :
- attribut data-category sur l'élément ou un de ses parents : imposée par le développeur du site ;
- dans un en-tête, un menu ou un pied de page (<header>, <nav>, <footer>) : catégorie fixe ;
- dans un bloc nommé par la page, c'est-à-dire visé par un lien du sommaire (<a href="#cfa">CFA</a>)
  ou affiché par une liste déroulante (id="table-b-traditionnel" pour <option value="b-traditionnel">) :
  le texte du lien ou de l'option, celui que voit le visiteur ;
- dans un tableau qui a un titre (<caption>, ou une seule cellule <th> sur sa première ligne) : ce titre ;
- sinon : le dernier titre (<h1> à <h3>) qui le précède dans la page, lui compris, ou « Autres ».
  Un sous-titre (titre qui suit un titre plus important dans le même bloc) ne compte pas.
"""

import html
import re

from content.html_tree import parse

LANDMARKS = {"header": "En-tête", "nav": "Menu", "footer": "Pied de page"}
HEADINGS = {"h1", "h2", "h3"}
# Un lien vers ces balises (« haut de page »…) ne nomme pas un bloc
NOT_BLOCKS = {"html", "body", "main", "header"}
OTHER = "Autres"
MAX_LENGTH = 120  # Garde-fou : l'interface raccourcit l'affichage

TAG_RE = re.compile(r"<[^>]*>")
SPACES_RE = re.compile(r"\s+")


def _walk(node):
    """Nœuds éléments sous node, dans l'ordre du document"""
    for child in node.children:
        if child.kind == "element":
            yield child
            yield from _walk(child)


def _text(content, node):
    """Texte d'un nœud, sans balises, espaces regroupés"""
    text = html.unescape(TAG_RE.sub(" ", content[node.inner_start:node.inner_end]))
    return SPACES_RE.sub(" ", text).strip()[:MAX_LENGTH]


def _ancestors(node):
    ancestor = node.parent
    while ancestor is not None and ancestor.kind == "element":
        yield ancestor
        ancestor = ancestor.parent


def _landmark(node):
    return next((LANDMARKS[a.tag] for a in _ancestors(node) if a.tag in LANDMARKS), None)


def _declared(node):
    """Catégorie imposée par un attribut data-category, sur l'élément ou un de ses parents"""
    for candidate in (node, *_ancestors(node)):
        value = SPACES_RE.sub(" ", candidate.attr("data-category") or "").strip()
        if value:
            return value
    return None


class _BlockNames:
    """Noms que la page donne à ses blocs : liens internes (par id) et options des listes (par valeur)"""

    def __init__(self, content, root):
        self.links = {}
        self.options = {}
        for node in _walk(root):
            href = node.attr("href") or ""
            if node.tag == "a" and len(href) > 1 and href.startswith("#"):
                self.links.setdefault(href[1:], (_text(content, node), node))
            elif node.tag == "option" and node.attr("value"):
                self.options.setdefault(node.attr("value"), _text(content, node))

    def name(self, block):
        block_id = block.attr("id") or ""
        if not block_id or block.tag in NOT_BLOCKS:
            return None
        text, link = self.links.get(block_id, (None, None))
        # Un lien placé dans le bloc qu'il vise (« retour en haut ») ne le nomme pas
        if text and block not in _ancestors(link):
            return text
        for value, text in self.options.items():
            if text and (block_id == value or block_id.endswith(("-" + value, "_" + value))):
                return text
        return None

    def of(self, node):
        if not (self.links or self.options):
            return None
        return next(filter(None, (self.name(a) for a in _ancestors(node))), None)


def _table_title(content, table):
    """Titre d'un tableau, ou None si ses cellules <th> sont des en-têtes de colonnes"""
    for child in _walk(table):
        if child.tag == "caption":
            return _text(content, child) or None
        if child.tag == "tr":
            cells = [cell for cell in child.children if cell.kind == "element" and cell.tag in ("th", "td")]
            if len(cells) == 1 and cells[0].tag == "th":
                return _text(content, cells[0]) or None
            return None
    return None


def _is_subtitle(node, previous):
    """Titre qui suit un titre plus important dans le même bloc (ex. : <h3> sous le <h2> d'une section)"""
    return previous is not None and previous.parent is node.parent and previous.tag < node.tag


def editable_categories(content):
    """Catégorie de chaque élément éditable, dans l'ordre des index"""
    root, editables = parse(content)
    names = _BlockNames(content, root)
    table_titles = {}  # Titre déjà calculé de chaque tableau (id du nœud)
    heading = OTHER  # Titre qui définit la catégorie courante, dans l'ordre du document
    previous = None  # Dernier titre rencontré
    categories = {}
    for node in _walk(root):
        landmark = _landmark(node)
        if node.tag in HEADINGS and not landmark:
            text = _text(content, node)
            if text and not _is_subtitle(node, previous):
                heading = text
            previous = node
        if node.editable_index is None:
            continue
        category = _declared(node) or landmark or names.of(node)
        if not category:
            table = next((a for a in _ancestors(node) if a.tag == "table"), None)
            if table is not None:
                if id(table) not in table_titles:
                    table_titles[id(table)] = _table_title(content, table)
                category = table_titles[id(table)]
        categories[node.editable_index] = category or heading
    return [categories[node.editable_index] for node in editables]
