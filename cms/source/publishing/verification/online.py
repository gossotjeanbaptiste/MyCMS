#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mise en ligne - Après un push, GitHub Pages met une à deux minutes à republier le site.
Une page est en ligne quand le site renvoie exactement le contenu du fichier local.
"""

import time
import urllib.request
from pathlib import Path

TIMEOUT = 10


def fetch(url):
    """Contenu d'une adresse, sans cache (None si le site ne répond pas)"""
    separator = "&" if "?" in url else "?"
    try:
        request = urllib.request.Request(f"{url}{separator}mycms={int(time.time())}",
                                         headers={"Cache-Control": "no-cache", "User-Agent": "MyCMS"})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except Exception:
        return None


def page_url(base_url, page):
    return f"{base_url}/" if page == "index.html" else f"{base_url}/{page}"


def online_status(base_url, repo_path, pages, get=None):
    """{"online": pages déjà en ligne, "waiting": pages pas encore à jour}. get : lecture d'une adresse (fetch)"""
    get = get or fetch
    status = {"online": [], "waiting": []}
    for page in pages:
        try:
            local = (Path(repo_path) / page).read_bytes()
        except OSError:
            continue  # Page supprimée depuis : rien à attendre
        remote = get(page_url(base_url, page))
        status["online" if remote is not None and remote.replace(b"\r\n", b"\n") == local.replace(b"\r\n", b"\n")
               else "waiting"].append(page)
    return status
