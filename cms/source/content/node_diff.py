#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparaison de nœuds pour la sauvegarde hybride : les nœuds identiques sont recopiés
depuis le fichier, les écarts sont réécrits, et le HTML nouveau est nettoyé.
"""

import html
import re
from difflib import SequenceMatcher

from content.html_tree import LOCK_TAG, norm

# Balises que l'éditeur peut créer ; tout autre balisage nouveau est retiré (son texte est gardé)
NEW_TAGS = {"b": "strong", "strong": "strong", "i": "em", "em": "em", "a": "a", "br": "br"}


class NodeDiff:
    """Comparaison et nettoyage, utilisés par HybridSaver (qui fournit content, editables,
    newline, _sigs, src, render_orig et render_outer)"""

    def _attrs_key(self, node):
        return tuple(sorted((key, norm(value)) for key, value in node.attrs))

    def _text(self, node, source):
        return norm(html.unescape(source[node.start:node.end]))

    def sig(self, node, source, is_new):
        """Signature complète : deux nœuds de même signature sont identiques"""
        key = (id(node), is_new)
        if key not in self._sigs:
            if node.kind == "text":
                value = ("t", self._text(node, source))
            elif node.kind == "other":
                value = ("o", norm(source[node.start:node.end]))
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
