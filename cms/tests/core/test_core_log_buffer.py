#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de core : tampon de journal numéroté (l'interface ne redemande que les nouvelles lignes)"""

from core.log_buffer import LogBuffer


def test_since_returns_only_new_lines():
    buffer = LogBuffer(5)
    for line in ("a", "b", "c"):
        buffer.append(line)
    assert buffer.since(0) == {"lines": ["a", "b", "c"], "total": 3, "reset": False}
    assert buffer.since(2) == {"lines": ["c"], "total": 3, "reset": False}
    assert buffer.since(3) == {"lines": [], "total": 3, "reset": False}  # Rien de nouveau : réponse vide


def test_since_after_old_lines_were_dropped():
    buffer = LogBuffer(2)
    for line in ("a", "b", "c", "d"):
        buffer.append(line)
    assert list(buffer) == ["c", "d"] and buffer.total == 4 and buffer[-1] == "d"
    assert buffer.since(3) == {"lines": ["d"], "total": 4, "reset": False}
    # Lignes perdues entre-temps : tout le tampon, à afficher à la place
    assert buffer.since(1) == {"lines": ["c", "d"], "total": 4, "reset": True}


def test_since_after_clear_or_restart():
    buffer = LogBuffer(5)
    buffer.append("a")
    buffer.clear()
    assert len(buffer) == 0 and buffer.since(1) == {"lines": [], "total": 1, "reset": False}
    buffer.append("b")
    assert buffer.since(1) == {"lines": ["b"], "total": 2, "reset": False}
    assert buffer.since(99) == {"lines": ["b"], "total": 2, "reset": True}  # Serveur relancé
