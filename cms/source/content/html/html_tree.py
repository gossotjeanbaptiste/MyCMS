#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arbre HTML - Chaque nœud garde ses positions exactes dans le texte source,
ce qui permet de recopier à l'octet près tout ce qui n'est pas modifié.
"""

import re
from html.parser import HTMLParser

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}

# Marqueur envoyé par l'éditeur à la place d'un élément éditable imbriqué (verrouillé)
LOCK_TAG = "mycms-lock"

# Éléments éditables dont on modifie l'attribut src (adresse), pas le contenu
SRC_TAGS = {"iframe", "img"}


class Node:
    """Nœud de l'arbre : positions [start, end) dans la source, [inner_start, inner_end) pour le contenu"""

    __slots__ = ("kind", "tag", "attrs", "start", "end", "inner_start", "inner_end",
                 "children", "parent", "editable_index")

    def __init__(self, kind, start, tag=None, attrs=None, parent=None):
        self.kind = kind  # root, element, text, other (commentaire, doctype...)
        self.tag = tag
        self.attrs = attrs or []
        self.start = start
        self.end = start
        self.inner_start = start
        self.inner_end = start
        self.children = []
        self.parent = parent
        self.editable_index = None

    def attr(self, name, default=None):
        for key, value in self.attrs:
            if key == name:
                return value
        return default

    def is_editable(self):
        return self.kind == "element" and "editable" in (self.attr("class") or "").split()


class _TreeBuilder(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", source)]
        self.root = Node("root", 0)
        self.root.end = self.root.inner_end = len(source)
        self.stack = [self.root]
        self.text = None
        self.editables = []

    def _offset(self):
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def _end_text(self, offset):
        if self.text is not None:
            self.text.end = self.text.inner_end = offset
            self.text = None

    def _add(self, node):
        node.parent = self.stack[-1]
        self.stack[-1].children.append(node)

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, self_closing=True)

    def _open(self, tag, attrs, self_closing):
        offset = self._offset()
        self._end_text(offset)
        node = Node("element", offset, tag, attrs)
        node.end = node.inner_start = node.inner_end = offset + len(self.get_starttag_text())
        self._add(node)
        if node.is_editable():
            node.editable_index = len(self.editables)
            self.editables.append(node)
        if not self_closing and tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        offset = self._offset()
        self._end_text(offset)
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                # Les éléments restés ouverts au-dessus se ferment ici (fermeture implicite)
                for unclosed in self.stack[depth + 1:]:
                    unclosed.inner_end = unclosed.end = offset
                node = self.stack[depth]
                node.inner_end = offset
                node.end = self.source.index(">", offset) + 1
                del self.stack[depth:]
                return
        # Balise fermante orpheline : ignorée

    def handle_data(self, data):
        offset = self._offset()
        if self.text is None:
            self.text = Node("text", offset)
            self._add(self.text)

    def _other(self, terminator):
        offset = self._offset()
        self._end_text(offset)
        node = Node("other", offset)
        end = self.source.find(terminator, offset)
        node.end = node.inner_end = (end + len(terminator)) if end >= 0 else len(self.source)
        self._add(node)

    def handle_comment(self, data):
        self._other("-->")

    def handle_decl(self, decl):
        self._other(">")

    def handle_pi(self, data):
        self._other(">")

    def unknown_decl(self, data):
        self._other("]]>")

    def close(self):
        super().close()
        self._end_text(len(self.source))
        for unclosed in self.stack[1:]:
            unclosed.inner_end = unclosed.end = len(self.source)


def parse(source):
    """(racine, éléments éditables dans l'ordre du document)"""
    builder = _TreeBuilder(source)
    builder.feed(source)
    builder.close()
    return builder.root, builder.editables


def norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def editable_sources(content):
    """Pour chaque élément éditable : son contenu source exact et les index des éléments éditables qu'il contient"""
    _, editables = parse(content)
    result = []
    for node in editables:
        nested = [e.editable_index for e in editables[node.editable_index + 1:] if e.start < node.end]
        result.append({"html": content[node.inner_start:node.inner_end], "nested": nested})
    return result
