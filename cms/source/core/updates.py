#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mises à jour - Une version plus récente de MyCMS est-elle publiée sur GitHub (releases) ?
Sans réseau, ou si GitHub ne répond pas : rien n'est signalé.
Téléchargement de son installeur (.msi), vérifié par sa taille et son empreinte SHA-256.
"""

import hashlib
import json
import re
import urllib.request
from pathlib import Path

RELEASES_URL = "https://api.github.com/repos/gossotjeanbaptiste/MyCMS/releases/latest"
TIMEOUT = 5
DOWNLOAD_TIMEOUT = 60
CHUNK = 1 << 16


def parse_version(text):
    """(2, 1, 5) pour "v2.1.5" ou "2.1.5", None si ce n'est pas un numéro de version"""
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(text or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def installer_asset(assets):
    """Le .msi joint à la release : {"name", "url", "size", "sha256"}, ou None. GitHub donne l'empreinte
    sous la forme "sha256:…" (champ digest), absent des anciennes releases"""
    for asset in assets or []:
        if str(asset.get("name", "")).lower().endswith(".msi"):
            digest = str(asset.get("digest") or "")
            return {"name": Path(asset["name"]).name, "url": asset["browser_download_url"], "size": asset["size"],
                    "sha256": digest.removeprefix("sha256:") if digest.startswith("sha256:") else None}
    return None


def fetch_latest():
    """Dernière release publiée : {"tag", "url", "installer"}, ou None (pas de réseau, pas de release, dépôt privé)"""
    request = urllib.request.Request(RELEASES_URL, headers={"Accept": "application/vnd.github+json",
                                                            "User-Agent": "MyCMS"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {"tag": data["tag_name"], "url": data["html_url"], "installer": installer_asset(data.get("assets"))}
    except Exception:
        return None


def update_info(current, latest):
    """Ce que l'interface affiche : {"available", "current", "latest", "url", "installer"}"""
    newer = latest is not None and (parse_version(latest["tag"]) or ()) > (parse_version(current) or ())
    return {
        "available": newer,
        "current": current,
        "latest": latest["tag"].lstrip("v") if newer else None,
        "url": latest["url"] if newer else None,
        "installer": latest.get("installer") if newer else None,
    }


def download(installer, folder):
    """Télécharge le .msi dans folder et renvoie son chemin. ValueError si le fichier reçu n'est pas le bon
    (taille ou empreinte différente) : il est alors supprimé"""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(installer["name"]).name
    digest = hashlib.sha256()
    request = urllib.request.Request(installer["url"], headers={"User-Agent": "MyCMS"})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, open(path, "wb") as file:
        while chunk := response.read(CHUNK):
            digest.update(chunk)
            file.write(chunk)
    expected = installer.get("sha256")
    if path.stat().st_size != installer["size"] or (expected and digest.hexdigest() != expected.lower()):
        path.unlink(missing_ok=True)
        raise ValueError("le fichier reçu est incomplet ou abîmé")
    return path
