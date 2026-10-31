#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Changements d'une page entre deux versions, élément éditable par élément éditable, pour l'historique :
textes modifiés (avec les mots changés), ajoutés ou supprimés.
"""

import html
import re
from difflib import SequenceMatcher

from content.categories import editable_categories
from content.html_tree import SRC_TAGS, editable_sources, parse
from content.published import align

TAG_RE = re.compile(r"<[^>]*>")
SPACES_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"\s+|\S+\s*")  # Un mot et les espaces qui le suivent : blocs plus lisibles
MAX_CHANGES = 100  # Par page (premier commit : toute la page est « ajoutée »)


def _elements(content):
    """Éléments éditables : balise, contenu source (pour les associer) et texte lisible"""
    if not content:
        return []
    _, editables = parse(content)
    sources = editable_sources(content)
    categories = editable_categories(content)
    result = []
    for node, source, category in zip(editables, sources, categories):
        if node.tag in SRC_TAGS:
            text = node.attr("src") or ""
        else:
            text = SPACES_RE.sub(" ", html.unescape(TAG_RE.sub(" ", source["html"]))).strip()
        result.append({"tag": node.tag, "html": source["html"], "text": text, "category": category})
    return result


def word_diff(before, after):
    """Segments [{op: equal | del | ins, text}] : les mots changés entre deux textes"""
    old, new = WORD_RE.findall(before), WORD_RE.findall(after)
    segments = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if op == "equal":
            segments.append({"op": "equal", "text": "".join(old[i1:i2])})
            continue
        if i2 > i1:
            segments.append({"op": "del", "text": "".join(old[i1:i2])})
        if j2 > j1:
            segments.append({"op": "ins", "text": "".join(new[j1:j2])})
    return segments


def element_changes(before_content, after_content):
    """Changements des éléments éditables d'une page : [{kind, tag, category, before, after, words}]
    kind : modified, formatted (mise en forme seule), added, removed. Retourne (changements, nombre total)"""
    before, after = _elements(before_content), _elements(after_content)
    matches = align([(e["tag"], e["html"]) for e in before], [(e["tag"], e["html"]) for e in after])
    changes = []
    for element, match in zip(after, matches):
        if match is None:
            changes.append({"kind": "added", "tag": element["tag"], "category": element["category"],
                            "before": "", "after": element["text"]})
        elif before[match]["html"] != element["html"]:
            old = before[match]["text"]
            # Même texte : seule la mise en forme (gras, lien…) a changé
            kind = "modified" if old != element["text"] else "formatted"
            changes.append({"kind": kind, "tag": element["tag"], "category": element["category"],
                            "before": old, "after": element["text"], "words": word_diff(old, element["text"])})
    matched = set(m for m in matches if m is not None)
    for index, element in enumerate(before):
        if index not in matched:
            changes.append({"kind": "removed", "tag": element["tag"], "category": element["category"],
                            "before": element["text"], "after": ""})
    return changes[:MAX_CHANGES], len(changes)
