#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tampon de journal numéroté - Les dernières lignes, et le nombre total de lignes reçues depuis le démarrage.
L'interface ne redemande que les nouvelles lignes (since) au lieu de tout le journal à chaque fois.
"""

from collections import deque


class LogBuffer:
    """Dernières lignes d'un journal ; total : lignes reçues depuis le démarrage (effacées comprises)"""

    def __init__(self, maxlen):
        self._lines = deque(maxlen=maxlen)
        self.total = 0

    def append(self, line):
        self._lines.append(line)
        self.total += 1

    def clear(self):
        self._lines.clear()

    def __iter__(self):
        return iter(self._lines)

    def __len__(self):
        return len(self._lines)

    def __getitem__(self, index):
        return self._lines[index]

    def since(self, seen):
        """Lignes reçues après les seen premières : {"lines", "total", "reset"}.
        reset : seen ne correspond plus (lignes effacées ou trop anciennes) ; lines contient alors tout le tampon."""
        first = self.total - len(self._lines)  # Numéro de la plus ancienne ligne gardée
        if not first <= seen <= self.total:
            return {"lines": list(self._lines), "total": self.total, "reset": True}
        return {"lines": list(self._lines)[seen - first:], "total": self.total, "reset": False}
