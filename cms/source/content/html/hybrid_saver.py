#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sauvegarde hybride des éléments éditables : les nœuds inchangés sont recopiés
tels quels depuis le fichier, seuls les écarts sont réécrits (et nettoyés).
"""

import html
import re

from content.html.html_tree import LOCK_TAG, SRC_TAGS, parse
from content.html.node_diff import NodeDiff


class HybridSaver(NodeDiff):
    """Applique les nouveaux contenus (HTML de l'éditeur) en ne réécrivant que les écarts"""

    def __init__(self, content, values):
        self.content = content
        self.root, self.editables = parse(content)
        self.newline = "\r\n" if "\r\n" in content else "\n"
        self.values = {}
        for index, value in values.items():
            if not 0 <= index < len(self.editables):
                continue
            node = self.editables[index]
            if node.tag in SRC_TAGS:
                if value != (node.attr("src") or ""):
                    self.values[index] = value
            else:
                self.values[index] = value
        self._sigs = {}
        self._new_roots = []
        self._touched = None

    # ======= Ce qui a changé =======

    def touched_nodes(self):
        """Éléments éditables modifiés, ou contenant un élément éditable modifié"""
        if self._touched is None:
            changed = [self.editables[i] for i in self.values]
            self._touched = {
                node.editable_index for node in self.editables
                if any(node.start <= c.start < node.end for c in changed)
            }
        return self._touched

    def _contains_touched(self, node):
        return any(node.start <= self.editables[i].start < node.end for i in self.touched_nodes())

    # ======= Rendu =======

    def src(self, node):
        return self.content[node.start:node.end]

    def render_outer(self, node):
        """Source complète d'un élément éditable, avec ses modifications"""
        if node.editable_index not in self.touched_nodes():
            return self.src(node)
        start_tag = self.content[node.start:node.inner_start]
        end_tag = self.content[node.inner_end:node.end]
        if node.tag in SRC_TAGS:
            if node.editable_index in self.values:
                start_tag = set_attribute(start_tag, "src", self.values[node.editable_index])
            return start_tag + self.content[node.inner_start:node.end]
        return start_tag + self.render_inner(node) + end_tag

    def render_inner(self, node):
        index = node.editable_index
        if index not in self.values:
            return "".join(self.render_orig(child) for child in node.children)

        new_root, _ = parse(self.values[index])
        # Garder l'arbre en vie : le cache des signatures est indexé par id(nœud)
        self._new_roots.append(new_root)
        self._check_locks(node, new_root)
        return self.diff_children(node.children, new_root.children, self.values[index])

    def render_orig(self, node):
        """Nœud d'origine recopié tel quel, sauf les éléments éditables modifiés qu'il contient"""
        if node.kind != "element" or not self._contains_touched(node):
            return self.src(node)
        if node.editable_index is not None:
            return self.render_outer(node)
        return (self.content[node.start:node.inner_start]
                + "".join(self.render_orig(child) for child in node.children)
                + self.content[node.inner_end:node.end])

    def _check_locks(self, node, new_root):
        """Chaque élément éditable imbriqué doit toujours être présent dans le nouveau contenu"""
        expected = {child.editable_index for child in self._direct_nested(node)}
        found = set()
        stack = list(new_root.children)
        while stack:
            current = stack.pop()
            if current.kind == "element" and current.tag == LOCK_TAG:
                found.add(int(current.attr("data-index", "-1")))
            stack.extend(current.children)
        missing = expected - found
        if missing:
            raise ValueError(f"L'élément éditable imbriqué [{min(missing)}] a été supprimé de l'élément [{node.editable_index}]")

    def _direct_nested(self, node):
        result = []
        stack = list(node.children)
        while stack:
            current = stack.pop()
            if current.editable_index is not None:
                result.append(current)
            else:
                stack.extend(current.children)
        return result

    # ======= Application =======

    def apply(self):
        """Nouveau contenu du fichier et nombre d'éléments modifiés"""
        touched = self.touched_nodes()
        edits = []
        for index in sorted(touched):
            node = self.editables[index]
            ancestor = node.parent
            while ancestor is not None and ancestor.editable_index not in touched:
                ancestor = ancestor.parent
            if ancestor is None:  # Élément modifié le plus extérieur : remplacé d'un bloc
                edits.append((node.start, node.end, self.render_outer(node)))

        content = self.content
        for start, end, replacement in sorted(edits, reverse=True):
            content = content[:start] + replacement + content[end:]
        return content, len(self.values)


def set_attribute(start_tag, name, value):
    """Remplacer (ou ajouter) la valeur d'un attribut dans une balise ouvrante"""
    quoted = '"' + html.escape(value, quote=True) + '"'
    pattern = rf'''(\s{re.escape(name)}\s*=\s*)("[^"]*"|'[^']*'|[^\s"'>]+)'''
    if re.search(pattern, start_tag, re.I):
        return re.sub(pattern, lambda m: m.group(1) + quoted, start_tag, count=1, flags=re.I)
    closing = '/>' if start_tag.endswith('/>') else '>'
    return start_tag[:-len(closing)] + f' {name}={quoted}' + closing
