#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : dupliquer ou supprimer depuis l'éditeur, images (envoi et vignettes)"""

import io

import pytest

from site_builder import read

TARIFS = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Tarifs</title></head>
<body>
    <ul>
        <li class="editable">Cours de code illimité</li>
        <li class="editable">Livre de code</li>
    </ul>
    <table>
        <tr><td class="editable">Inscription</td><td class="editable" id="prix">70€</td></tr>
    </table>
    <img class="editable" alt="Voiture" src="../images/voiture.png">
</body></html>
"""
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def tarifs(site_client, git_site):
    (git_site / "images").mkdir()
    (git_site / "images" / "voiture.png").write_bytes(PNG)
    (git_site / "page" / "tarifs.html").write_bytes(TARIFS.replace("\n", "\r\n").encode("utf-8"))
    return git_site / "page" / "tarifs.html"


def load(client):
    return client.get("/api/files/page/tarifs.html").get_json()


def change(client, action, index, data=None):
    data = data or load(client)
    return client.post("/api/structure/page/tarifs.html", json={"hash": data["hash"], "action": action, "index": index})


def test_load_tells_what_can_be_repeated(site_client, tarifs):
    elements = load(site_client)["elements"]
    assert [e["repeat"] for e in elements] == ["li", "li", "tr", "tr", None]
    assert elements[4]["is_image"] and elements[4]["value"] == "../images/voiture.png"


def test_duplicate_and_delete(site_client, tarifs):
    result = change(site_client, "duplicate", 1).get_json()
    assert result["message"] == "Élément de liste dupliqué dans page/tarifs.html" and result["focus"] == 2
    assert read(tarifs).count("Livre de code") == 2 and len(load(site_client)["elements"]) == 6
    assert result["hash"] == load(site_client)["hash"]
    result = change(site_client, "duplicate", 4).get_json()
    assert result["message"] == "Ligne dupliquée dans page/tarifs.html" and 'id="prix-2"' in read(tarifs)
    assert change(site_client, "delete", 2).get_json()["message"] == "Élément de liste supprimé dans page/tarifs.html"
    assert read(tarifs).count("Livre de code") == 1


def test_structure_refusals(site_client, tarifs):
    data = load(site_client)
    assert change(site_client, "move", 0, data).get_json()["error"] == "Action inconnue"
    assert change(site_client, "delete", 2, data).get_json()["error"] == "Impossible de supprimer la dernière ligne du tableau"
    assert "ni dans une liste" in change(site_client, "duplicate", 4, data).get_json()["error"]
    assert change(site_client, "duplicate", 99, data).get_json()["error"] == "Élément introuvable"
    stale = site_client.post("/api/structure/page/tarifs.html", json={"hash": "x", "action": "duplicate", "index": 0})
    assert stale.status_code == 409
    assert site_client.post("/api/structure/absent.html", json={}).status_code == 404


def upload(client, filename, data=PNG, page="page/tarifs.html"):
    return client.post("/api/images", data={"page": page, "file": (io.BytesIO(data), filename)},
                       content_type="multipart/form-data")


def test_upload_image(site_client, tarifs, git_site):
    result = upload(site_client, "Photo équipe.PNG").get_json()
    assert result == {"success": True, "src": "../images/Photo_equipe.PNG", "path": "images/Photo_equipe.PNG",
                      "lighter": ""}
    assert (git_site / "images" / "Photo_equipe.PNG").read_bytes() == PNG
    assert upload(site_client, "Photo équipe.PNG").get_json()["src"] == "../images/Photo_equipe-2.PNG"
    assert upload(site_client, "logo.png", page="index.html").get_json()["src"] == "images/logo.png"


@pytest.mark.parametrize("filename, page, status, message", [
    ("script.svg", "page/tarifs.html", 400, "Format non accepté"),
    ("", "page/tarifs.html", 400, "Aucune image reçue"),
    ("a.png", "absent.html", 404, "Fichier introuvable"),
])
def test_upload_refusals(site_client, tarifs, filename, page, status, message):
    response = upload(site_client, filename, page=page)
    assert response.status_code == status and message in response.get_json()["error"]


def test_upload_too_large(site_client, tarifs):
    response = upload(site_client, "grande.png", data=b"0" * (10 * 1024 * 1024 + 1))
    assert response.status_code == 413


def test_site_image(site_client, tarifs):
    url = "/api/site-image?page=page/tarifs.html&src="
    response = site_client.get(url + "../images/voiture.png")
    assert response.status_code == 200 and response.data == PNG
    assert site_client.get(url + "/images/voiture.png").status_code == 200  # Adresse depuis la racine
    for src in ("../../../secret.png", "https://exemple.fr/a.png", "../index.html", "../images/absente.png", ""):
        assert site_client.get(url + src).status_code == 404
    assert site_client.get("/api/site-image?page=absent.html&src=a.png").status_code == 404


def test_new_image_is_saved_in_the_page(site_client, tarifs):
    src = upload(site_client, "nouvelle.png").get_json()["src"]
    data = load(site_client)
    assert site_client.post("/api/files/page/tarifs.html", json={"hash": data["hash"], "values": {"4": src}}).status_code == 200
    assert '<img class="editable" alt="Voiture" src="../images/nouvelle.png">' in read(tarifs)
