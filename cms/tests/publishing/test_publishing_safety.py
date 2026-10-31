#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : vérification avant publication et suivi de la mise en ligne"""

import http.server
import threading

import pytest

from publishing.checks import check_page, check_pages
from publishing.online import fetch, online_status, page_url

PAGE = """<html><body id="haut">
<a href="../style/style.css">ok</a> <a href="/index.html">ok</a> <a href="../index.html#titre">ok</a>
<a href="#haut">ok</a> <a href="#">ok</a> <a href="#top">ok</a> <a href="https://exemple.fr/absent">externe</a>
<a href="mailto:contact@rout-art.fr">ok</a> <a href="tel:+33 3 89 00 00 00">ok</a> <a href="javascript:void(0)">js</a>
<a href="../files/absent.pdf">cassé</a>
<a href="#inconnue">ancre</a>
<a href="mailto:contact.rout-art.fr">mail</a>
<a href="tel:appelez-nous">tel</a>
<img src="../images/absente.png">
<p class="editable">  </p>
<p class="editable"><img src="../style/style.css"></p>
<img class="editable" src="">
</body></html>"""


def messages(problems):
    return [(p["line"], p["message"]) for p in problems]


def test_check_page(site):
    assert messages(check_page(site, "page/test.html", PAGE)) == [
        (5, "Fichier introuvable : ../files/absent.pdf"),
        (6, "Ancre introuvable dans la page : #inconnue"),
        (7, "Adresse e-mail incorrecte : mailto:contact.rout-art.fr"),
        (8, "Numéro de téléphone incorrect : tel:appelez-nous"),
        (9, "Fichier introuvable : ../images/absente.png"),
        (10, "Élément vide (élément [0])"),
        (12, "Adresse vide (élément [2])"),
    ]


def test_links_are_resolved_like_a_browser(site):
    # Depuis la racine, ../ ne remonte pas au-dessus du site ; un dossier vise son index.html
    content = '<a href="../style/style.css">a</a> <a href="./">b</a> <a href="page/">c</a>'
    assert messages(check_page(site, "index.html", content)) == [(1, "Fichier introuvable : page/")]


def test_test_site_has_no_problem(site):
    pages = ["index.html", "page/formations.html", "page/financement.html", "page/mentions.html"]
    assert check_pages(site, pages + ["absente.html"]) == []


# ======= Mise en ligne =======

def test_page_url():
    assert page_url("https://site.fr", "index.html") == "https://site.fr/"
    assert page_url("https://site.fr", "page/a.html") == "https://site.fr/page/a.html"


def test_online_status(site):
    local = (site / "index.html").read_bytes()
    served = {"https://site.fr/": local.replace(b"\r\n", b"\n"),  # Fins de ligne ignorées
              "https://site.fr/page/formations.html": b"ancienne version"}
    status = online_status("https://site.fr", site, ["index.html", "page/formations.html",
                                                     "page/financement.html", "page/supprimee.html"], served.get)
    assert status == {"online": ["index.html"], "waiting": ["page/formations.html", "page/financement.html"]}


def test_fetch_without_cache():
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers["Cache-Control"]))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"contenu")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert fetch(f"http://127.0.0.1:{server.server_port}/page.html") == b"contenu"
    finally:
        server.shutdown()
        server.server_close()
    assert seen[0][0].startswith("/page.html?mycms=") and seen[0][1] == "no-cache"
    assert fetch(f"http://127.0.0.1:{server.server_port}/page.html") is None  # Serveur arrêté


@pytest.mark.parametrize("url", ["http://127.0.0.1:1/x", "pas une adresse"])
def test_fetch_errors_return_none(url):
    assert fetch(url) is None
