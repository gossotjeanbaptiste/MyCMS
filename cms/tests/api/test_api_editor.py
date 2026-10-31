#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests fonctionnels : onglet Éditeur (pages, chargement, sauvegarde, extraits de code)"""

import pytest

from site_builder import PAGES, read

LOCK = '<mycms-lock data-index="4"></mycms-lock>'


def load(client, page="index.html"):
    response = client.get(f"/api/files/{page}")
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def save(client, page, data, values):
    return client.post(f"/api/files/{page}", json={"hash": data["hash"], "values": values})


def test_list_pages(site_client):
    assert site_client.get("/api/files").get_json() == {"success": True, "files": PAGES}


def test_list_pages_without_site(client, services, tmp_path):
    services.config.set_repo_path(str(tmp_path / "absent"))
    assert client.get("/api/files").get_json()["files"] == []


def test_load_page(site_client):
    data = load(site_client)
    elements = data["elements"]
    assert len(elements) == 8 and data["published_known"] is True and len(data["hash"]) == 40
    intro = elements[2]
    assert intro["tag"] == "p" and intro["id"] == "intro" and intro["category"] == "Bienvenue à l'auto-école"
    assert intro["html"].startswith("Le <strong>permis</strong>") and intro["value"].startswith("Le permis")
    assert elements[3]["nested"] == [4] and elements[5]["is_iframe"]
    assert [e["bold"] for e in elements] == [False] * 6 + [True, False]
    assert ".highlight" in data["bold_selectors"]
    assert all(e["published_html"] == e["html"] for e in elements)  # Rien de modifié depuis le dernier push


@pytest.mark.parametrize("page", ["absent.html", "page/../index.html", "style/style.css"])
def test_only_site_pages_can_be_opened(site_client, page):
    assert site_client.get(f"/api/files/{page}").status_code == 404
    assert site_client.post(f"/api/files/{page}", json={}).status_code == 404


def test_page_without_editable_elements(site_client, git_site):
    (git_site / "page" / "vide.html").write_text("<p>Rien à modifier</p>", encoding="utf-8")
    data = load(site_client, "page/vide.html")
    assert data["elements"] == [] and "Aucun élément éditable" in data["notice"]


def test_save_writes_only_the_change_and_updates_sitemap(site_client, git_site):
    before = read(git_site / "index.html")
    data = load(site_client)
    response = save(site_client, "index.html", data, {"1": "Bienvenue chez MyCMS"})
    result = response.get_json()
    assert result["message"] == "Fichier sauvegardé: index.html (1 élément(s) modifié(s))"
    assert result["sitemap"] == "Sitemap créé à la racine : 3 pages, 2 exclues (page/mentions.html, page/prive/secret.html)"
    after = read(git_site / "index.html")
    assert after == before.replace("Bienvenue à l'auto-école</h1>", "Bienvenue chez MyCMS</h1>")
    assert result["hash"] == load(site_client)["hash"]


def test_unchanged_round_trip_is_byte_identical(site_client, git_site):
    for page in ("index.html", "page/formations.html", "page/financement.html", "page/mentions.html"):
        before = (git_site / page).read_bytes()
        data = load(site_client, page)
        values = {str(e["index"]): (e["value"] if e["is_iframe"] else e["html"]) for e in data["elements"]
                  if not e["nested"]}
        assert save(site_client, page, data, values).status_code == 200
        assert (git_site / page).read_bytes() == before


def test_save_refused_when_file_changed_since_loading(site_client, git_site):
    data = load(site_client)
    (git_site / "index.html").write_bytes((git_site / "index.html").read_bytes() + b"\r\n")
    response = save(site_client, "index.html", data, {"1": "Titre"})
    assert response.status_code == 409 and "modifié depuis son chargement" in response.get_json()["error"]


def test_save_refused_when_nested_element_removed(site_client, git_site):
    before = read(git_site / "index.html")
    response = save(site_client, "index.html", load(site_client), {"3": "Le verrou a disparu"})
    assert response.status_code == 500 and "imbriqué [4] a été supprimé" in response.get_json()["error"]
    assert read(git_site / "index.html") == before


def test_saving_twice_without_reloading(site_client):
    data = load(site_client)
    first = save(site_client, "index.html", data, {"1": "Un"}).get_json()
    assert save(site_client, "index.html", {"hash": first["hash"]}, {"1": "Deux"}).status_code == 200


def test_published_version_after_saving(site_client):
    save(site_client, "index.html", load(site_client), {"7": "© 2027"})
    footer = load(site_client)["elements"][7]
    assert footer["html"] == "© 2027" and footer["published_html"] == "© 2026 Auto-école"
    assert footer["published_value"] == "© 2026 Auto-école"


def test_published_version_unknown_without_git(site_client, services):
    services.git_found = False
    assert load(site_client)["published_known"] is False


def test_snippet_shows_code_without_writing(site_client, git_site):
    before = read(git_site / "index.html")
    data = load(site_client)
    response = site_client.post("/api/snippet/index.html", json={"hash": data["hash"], "values": {"3": f"Nouveau {LOCK}"},
                                                                  "index": 3})
    snippet = response.get_json()
    assert snippet["success"] and snippet["start_line"] == 16
    assert any("Nouveau <span" in line for line in snippet["lines"])
    assert read(git_site / "index.html") == before


def test_snippet_errors(site_client):
    data = load(site_client)
    url = "/api/snippet/index.html"
    assert site_client.post(url, json={"hash": "ancien", "values": {}, "index": 1}).status_code == 409
    assert site_client.post(url, json={"hash": data["hash"], "values": {}, "index": 99}).status_code == 404
    assert site_client.post(url, json={"hash": data["hash"], "values": {"3": "x"}, "index": 3}).status_code == 500
    assert site_client.post("/api/snippet/absent.html", json={}).status_code == 404
