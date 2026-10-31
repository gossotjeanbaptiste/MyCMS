#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aller-retour complet sans modification : page chargée par l'API, passée par les vraies fonctions
de l'éditeur (buildRichEditor puis serializeRich, dans Node avec jsdom), renvoyée telle quelle :
le fichier doit rester identique à l'octet près.

Sur le site de test, et sur une copie du vrai site si MYCMS_SITE donne son chemin :
    set MYCMS_SITE=C:\\chemin\\du\\site
Le vrai site n'est jamais modifié : il est copié dans un dossier temporaire.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import CMS_DIR

WEB_DIR = CMS_DIR / "web"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(not NODE or not (WEB_DIR / "node_modules" / "jsdom").is_dir(),
                                reason="Node et jsdom nécessaires (cd cms/web && npm install)")


def editor_values(elements):
    """Valeurs que l'éditeur du navigateur renverrait pour ces éléments, sans modification"""
    result = subprocess.run([NODE, "tests/roundtrip-cli.mjs"], cwd=WEB_DIR, input=json.dumps(elements),
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def round_trip(client, root):
    """Aller-retour sur chaque page ; retourne le nombre d'éléments renvoyés"""
    sent = 0
    for page in client.get("/api/files").get_json()["files"]:
        before = (root / page).read_bytes()
        data = client.get(f"/api/files/{page}").get_json()
        if not data["elements"]:
            continue
        values = editor_values(data["elements"])
        response = client.post(f"/api/files/{page}", json={"hash": data["hash"], "values": values})
        assert response.status_code == 200, (page, response.get_json())
        assert (root / page).read_bytes() == before, f"{page} a changé après un aller-retour sans modification"
        sent += len(values)
    return sent


def test_round_trip_on_test_site(site_client, git_site):
    assert round_trip(site_client, git_site) == 27  # Tous les éléments des 5 pages


@pytest.mark.skipif(not os.environ.get("MYCMS_SITE"), reason="MYCMS_SITE non défini (chemin du vrai site)")
def test_round_trip_on_real_site(client, services, tmp_path):
    source = Path(os.environ["MYCMS_SITE"])
    copy = tmp_path / "copie-du-site"
    shutil.copytree(source, copy, ignore=shutil.ignore_patterns(".git", "node_modules"))
    services.config.set_repo_path(str(copy))
    assert round_trip(client, copy) > 0
