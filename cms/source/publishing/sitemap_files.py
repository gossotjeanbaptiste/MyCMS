#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fichier sitemap.xml - Emplacement dans le site et réglages déjà présents
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from content.page_finder import find_files


def find_sitemap(repo_path):
    """Chemin du sitemap.xml : à la racine en priorité, sinon le premier trouvé"""
    repo_path = Path(repo_path)
    if (repo_path / "sitemap.xml").exists():
        return repo_path / "sitemap.xml"
    found = sorted(find_files(repo_path, lambda name: name.lower() == "sitemap.xml"),
                   key=lambda p: p.count("/"))
    return repo_path / found[0] if found else None


def read_existing(sitemap_path, logger):
    """Réglages (changefreq, priority) du sitemap existant, par URL"""
    try:
        root = ET.parse(sitemap_path).getroot()
    except Exception as e:
        logger.log(f"Sitemap existant illisible, il sera régénéré: {e}")
        return {}
    entries = {}
    for url in root.iter():
        if url.tag.rsplit("}", 1)[-1] != "url":
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: (child.text or "").strip() for child in url}
        if fields.get("loc"):
            entries[fields["loc"]] = fields
    return entries
