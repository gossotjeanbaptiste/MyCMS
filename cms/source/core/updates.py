#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mises à jour - Une version plus récente de MyCMS est-elle publiée sur GitHub (releases) ?
Sans réseau, ou si GitHub ne répond pas : rien n'est signalé.
"""

import json
import re
import urllib.request

RELEASES_URL = "https://api.github.com/repos/gossotjeanbaptiste/MyCMS/releases/latest"
TIMEOUT = 5


def parse_version(text):
    """(2, 1, 5) pour "v2.1.5" ou "2.1.5", None si ce n'est pas un numéro de version"""
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(text or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def fetch_latest():
    """Dernière release publiée : {"tag", "url"}, ou None (pas de réseau, pas de release, dépôt privé)"""
    request = urllib.request.Request(RELEASES_URL, headers={"Accept": "application/vnd.github+json",
                                                            "User-Agent": "MyCMS"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {"tag": data["tag_name"], "url": data["html_url"]}
    except Exception:
        return None


def update_info(current, latest):
    """Ce que l'interface affiche : {"available", "current", "latest", "url"}"""
    newer = latest is not None and (parse_version(latest["tag"]) or ()) > (parse_version(current) or ())
    return {
        "available": newer,
        "current": current,
        "latest": latest["tag"].lstrip("v") if newer else None,
        "url": latest["url"] if newer else None,
    }
