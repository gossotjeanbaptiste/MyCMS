#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version publiée de chaque élément éditable (marqueurs +/−/~ et bouton « Version en ligne »).

Les éléments sont associés par leur contenu, pas par leur position : après l'ajout ou la suppression
d'un élément de liste ou d'une ligne de tableau, les suivants gardent leur propre version publiée.
"""

from difflib import SequenceMatcher

MAX_COMPARISONS = 2500


def _similarity(a, b):
    """Ressemblance de deux clés : (balise, contenu) ; balises différentes : aucune"""
    if isinstance(a, tuple):
        if a[0] != b[0]:
            return 0.0
        a, b = a[1], b[1]
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _best_pairs(published, current):
    """Bloc modifié : associe chaque élément du côté le plus court à un élément de l'autre côté, dans l'ordre,
    en rendant les contenus les plus semblables possible. Retourne [(i, j)] (index dans le bloc)."""
    short, long_, swapped = (published, current, False) if len(published) <= len(current) else (current, published, True)
    n, m = len(short), len(long_)
    # best[i][j] : meilleur score pour associer short[i:] à des éléments de long_[j:]
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        best[i][m] = float("-inf")
        for j in range(m - 1, -1, -1):
            best[i][j] = max(_similarity(short[i], long_[j]) + best[i + 1][j + 1], best[i][j + 1])
    pairs, j = [], 0
    for i in range(n):
        while best[i][j] != _similarity(short[i], long_[j]) + best[i + 1][j + 1]:
            j += 1
        pairs.append((j, i) if swapped else (i, j))
        j += 1
    return pairs


def align(published, current):
    """Pour chaque élément actuel, l'index de l'élément publié correspondant, ou None (élément nouveau).
    published et current : listes de clés comparables (balise et contenu source)."""
    result = [None] * len(current)
    matcher = SequenceMatcher(None, published, current, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for offset in range(j2 - j1):
                result[j1 + offset] = i1 + offset
        elif tag == "replace":
            # Des éléments ajoutés ou supprimés, et d'autres modifiés : les plus proches se correspondent
            # (très gros bloc réécrit : dans l'ordre, pour garder un chargement rapide)
            if (i2 - i1) * (j2 - j1) <= MAX_COMPARISONS:
                pairs = _best_pairs(published[i1:i2], current[j1:j2])
            else:
                pairs = [(k, k) for k in range(min(i2 - i1, j2 - j1))]
            for i, j in pairs:
                result[j1 + j] = i1 + i
    return result


def published_versions(current, published):
    """current, published : éléments {tag, html, value} de la page actuelle et de la version publiée.
    Retourne pour chaque élément actuel (html publié, valeur publiée), ou (None, None) s'il est nouveau."""
    matches = align([(e["tag"], e["html"]) for e in published], [(e["tag"], e["html"]) for e in current])
    return [(None, None) if m is None else (published[m]["html"], published[m]["value"]) for m in matches]
