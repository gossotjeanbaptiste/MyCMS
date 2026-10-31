#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structure de la page - Dupliquer ou supprimer un élément de liste (<li>) ou une ligne de tableau (<tr>)
à partir d'un élément éditable. Seul ce bloc est copié ou retiré : le reste du fichier est recopié tel quel.

- Élément de liste : l'élément éditable est un <li>, ou se trouve dans un <li> (avant toute cellule).
- Ligne de tableau : l'élément éditable est une cellule (<td>, <th>).
"""

import re

from content.html_tree import parse

# Ce qu'on ne peut pas supprimer
LAST = {"li": "le dernier élément de la liste", "tr": "la dernière ligne du tableau"}
ID_RE = re.compile(r"""(\sid\s*=\s*)(["'])(.*?)\2""", re.I)


def _target(node):
    """Bloc à dupliquer ou supprimer pour cet élément éditable, ou None"""
    if node.tag in ("td", "th"):
        row = node.parent
        return row if row is not None and row.tag == "tr" else None
    current = node
    while current is not None and current.kind == "element":
        if current.tag == "li":
            return current
        if current.tag in ("td", "th", "table", "ul", "ol"):
            return None
        current = current.parent
    return None


def repeatable(content):
    """Pour chaque élément éditable : "li", "tr" ou None"""
    _, editables = parse(content)
    return [(target.tag if (target := _target(node)) is not None else None) for node in editables]


def _block(content, index):
    _, editables = parse(content)
    if not 0 <= index < len(editables):
        raise ValueError("Élément introuvable")
    target = _target(editables[index])
    if target is None:
        raise ValueError("Cet élément n'est ni dans une liste ni une cellule de tableau")
    return target


def _line_start(content, position):
    """Début de la ligne si seuls des espaces précèdent position sur cette ligne, sinon None"""
    start = content.rfind("\n", 0, position) + 1
    return start if not content[start:position].strip() else None


def _unique_ids(copy, content):
    """Les id de la copie reçoivent un suffixe (-2, -3…) : deux éléments ne doivent pas avoir le même id"""
    taken = set(m.group(3) for m in ID_RE.finditer(content))

    def rename(match):
        number = 2
        while f"{match.group(3)}-{number}" in taken:
            number += 1
        new_id = f"{match.group(3)}-{number}"
        taken.add(new_id)
        return f"{match.group(1)}{match.group(2)}{new_id}{match.group(2)}"

    return ID_RE.sub(rename, copy)


def duplicate(content, index):
    """Copie du bloc juste après lui, sur sa propre ligne avec la même indentation.
    Retourne (nouveau contenu, index du premier élément éditable de la copie)"""
    target = _block(content, index)
    copy = _unique_ids(content[target.start:target.end], content)
    line = _line_start(content, target.start)
    newline = "\r\n" if "\r\n" in content else "\n"
    separator = newline + content[line:target.start] if line is not None else " "
    new_content = content[:target.end] + separator + copy + content[target.end:]
    _, editables = parse(new_content)
    first = next(e.editable_index for e in editables if e.start >= target.end + len(separator))
    return new_content, first


def remove(content, index):
    """Retirer le bloc (et sa ligne s'il est seul dessus). Refusé pour le dernier de sa liste ou de son tableau"""
    target = _block(content, index)
    siblings = [child for child in target.parent.children if child.kind == "element" and child.tag == target.tag]
    if len(siblings) < 2:
        raise ValueError(f"Impossible de supprimer {LAST[target.tag]}")
    line = _line_start(content, target.start)
    start = target.start
    if line is not None:
        # Retirer aussi le retour à la ligne qui précède et l'indentation
        start = content.rfind("\n", 0, line)
        start = start - 1 if start > 0 and content[start - 1] == "\r" else start
        start = max(start, 0)
    return content[:start] + content[target.end:]
