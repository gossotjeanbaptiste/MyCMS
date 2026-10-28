#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recherche des pages - Détection automatique des fichiers HTML du site
"""

import os
from pathlib import Path

# Dossiers jamais parcourus (en plus des dossiers cachés comme .git)
EXCLUDED_DIRS = {"node_modules", "__pycache__"}


def find_files(repo_path, predicate):
    """Chemins relatifs (format a/b/c) des fichiers du repository qui satisfont predicate(nom)"""
    repo_path = Path(repo_path)
    found = []
    for root, dirs, files in os.walk(repo_path):
        # Élaguer sur place pour que os.walk ne descende pas dans ces dossiers
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in EXCLUDED_DIRS]
        for name in files:
            if predicate(name):
                found.append((Path(root) / name).relative_to(repo_path).as_posix())
    return found


def find_html_pages(repo_path):
    """Toutes les pages HTML du site, index.html de la racine en premier"""
    pages = find_files(repo_path, lambda name: name.lower().endswith((".html", ".htm")))
    return sorted(pages, key=lambda p: (p != "index.html", p.count("/"), p.lower()))
