#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Source HTML - Arbre HTML avec les positions exactes de chaque nœud dans le texte source,
et sauvegarde "hybride" des éléments éditables : les nœuds inchangés sont recopiés
tels quels depuis le fichier, seuls les écarts sont réécrits (et nettoyés).
"""

import html
import re
from difflib import SequenceMatcher
from html.parser import HTMLParser

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}

# Balises que l'éditeur peut créer ; tout autre balisage nouveau est retiré (son texte est gardé)
NEW_TAGS = {"b": "strong", "strong": "strong", "i": "em", "em": "em", "a": "a", "br": "br"}

# Marqueur envoyé par l'éditeur à la place d'un élément éditable imbriqué (verrouillé)
LOCK_TAG = "mycms-lock"


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


def _norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def editable_sources(content):
    """Pour chaque élément éditable : son contenu source exact et les index des éléments éditables qu'il contient"""
    _, editables = parse(content)
    result = []
    for node in editables:
        nested = [e.editable_index for e in editables[node.editable_index + 1:] if e.start < node.end]
        result.append({"html": content[node.inner_start:node.inner_end], "nested": nested})
    return result


class HybridSaver:
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
            if node.tag == "iframe":
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
        if node.tag == "iframe":
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

    # ======= Comparaison =======

    def _attrs_key(self, node):
        return tuple(sorted((key, _norm(value)) for key, value in node.attrs))

    def _text(self, node, source):
        return _norm(html.unescape(source[node.start:node.end]))

    def sig(self, node, source, is_new):
        """Signature complète : deux nœuds de même signature sont identiques"""
        key = (id(node), is_new)
        if key not in self._sigs:
            if node.kind == "text":
                value = ("t", self._text(node, source))
            elif node.kind == "other":
                value = ("o", _norm(source[node.start:node.end]))
            elif is_new and node.tag == LOCK_TAG:
                value = ("lock", int(node.attr("data-index", "-1")))
            elif not is_new and node.editable_index is not None:
                value = ("lock", node.editable_index)
            else:
                value = ("e", node.tag, self._attrs_key(node),
                         tuple(self.sig(child, source, is_new) for child in node.children))
            self._sigs[key] = value
        return self._sigs[key]

    def shape(self, node, source, is_new):
        """Forme : même type de nœud, même balise, mêmes attributs (le contenu peut différer)"""
        signature = self.sig(node, source, is_new)
        if signature[0] in ("lock", "o"):
            return signature
        if signature[0] == "t":
            return ("t",)
        return ("e", node.tag, self._attrs_key(node))

    def diff_children(self, old_nodes, new_nodes, new_source):
        old_sigs = [self.sig(n, self.content, False) for n in old_nodes]
        new_sigs = [self.sig(n, new_source, True) for n in new_nodes]
        out = []
        matcher = SequenceMatcher(None, old_sigs, new_sigs, autojunk=False)
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                out.extend(self.render_orig(n) for n in old_nodes[i1:i2])
            else:
                out.append(self._gap(old_nodes[i1:i2], new_nodes[j1:j2], new_source))
        return "".join(out)

    def _gap(self, old_nodes, new_nodes, new_source):
        """Zone qui diffère : les nœuds de même forme sont comparés plus finement, le reste est nouveau"""
        old_shapes = [self.shape(n, self.content, False) for n in old_nodes]
        new_shapes = [self.shape(n, new_source, True) for n in new_nodes]
        out = []
        matcher = SequenceMatcher(None, old_shapes, new_shapes, autojunk=False)
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                for old, new in zip(old_nodes[i1:i2], new_nodes[j1:j2]):
                    out.append(self._pair(old, new, new_source))
            else:
                # Les nœuds d'origine de cette zone sont retirés, les nouveaux sont nettoyés
                for position, new in enumerate(new_nodes[j1:j2]):
                    out.append(self.sanitize(new, new_source, first=(j1 + position == 0)))
        return "".join(out)

    def _pair(self, old, new, new_source):
        if old.kind == "text":
            return self.write_text(self._text(new, new_source))
        if old.kind == "other":
            return self.src(old)
        if old.editable_index is not None:
            return self.render_outer(old)
        # Même balise et mêmes attributs : balises d'origine gardées, contenu comparé récursivement
        return (self.content[old.start:old.inner_start]
                + self.diff_children(old.children, new.children, new_source)
                + self.content[old.inner_end:old.end])

    # ======= Nouveau contenu =======

    def write_text(self, text):
        escaped = html.escape(text, quote=False).replace(" ", "&nbsp;")
        return escaped.replace("\n", self.newline)

    def sanitize(self, node, source, first):
        """HTML nouveau : seules les balises de NEW_TAGS sont gardées"""
        if node.kind == "text":
            return self.write_text(self._text(node, source))
        if node.kind != "element":
            return ""
        if node.tag == LOCK_TAG:
            return self.render_outer(self.editables[int(node.attr("data-index", "-1"))])

        children = "".join(self.sanitize(child, source, first=(i == 0)) for i, child in enumerate(node.children))
        tag = NEW_TAGS.get(node.tag)
        if tag == "br":
            return "<br>"
        if tag == "a":
            href = (node.attr("href") or "").strip()
            if not href or re.match(r"(?i)\s*(javascript|vbscript|data):", href):
                return children
            return f'<a href="{html.escape(href, quote=True)}">{children}</a>'
        if tag:
            return f"<{tag}>{children}</{tag}>"
        # Retour à la ligne de l'éditeur (<div>, <p>) : devient un <br>
        if node.tag in ("div", "p") and not first:
            return "<br>" + children
        return children

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
