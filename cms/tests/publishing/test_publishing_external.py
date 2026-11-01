#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : liens externes vérifiés sur demande (serveur local, sans Internet)"""

import http.server
import threading

import pytest

from conftest import free_port
from publishing.verification import external

# Réponse du serveur local selon le chemin ; HEAD refusé sur /head-refuse
STATUS = {"/ok": 200, "/absent": 404, "/supprime": 410, "/robots": 403, "/trop": 429, "/head-refuse": 200,
          "/erreur": 500}


@pytest.fixture
def server():
    class Handler(http.server.BaseHTTPRequestHandler):
        def answer(self, body):
            code = STATUS.get(self.path.split("?")[0], 404)
            if self.command == "HEAD" and self.path in ("/head-refuse", "/robots"):
                code = 405 if self.path == "/head-refuse" else 403
            self.send_response(code)
            self.end_headers()
            if body:
                self.wfile.write(b"ok")

        def do_HEAD(self):
            self.answer(False)

        def do_GET(self):
            self.answer(True)

        def log_message(self, *args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


@pytest.mark.parametrize("path, expected", [
    ("/ok", None), ("/robots", None), ("/trop", None), ("/head-refuse", None), ("/erreur", None),
    ("/absent", "page introuvable (404)"), ("/supprime", "page supprimée (410)")])
def test_link_error(server, path, expected):
    assert external.link_error(server + path) == expected


def test_unreachable_sites():
    assert external.link_error(f"http://127.0.0.1:{free_port()}/") .startswith("site injoignable")
    assert external.link_error("https://site-qui-n-existe-pas.invalid/") == "site introuvable (l'adresse n'existe plus ?)"


def test_check_external(site, server):
    page = site / "page" / "liens.html"
    page.write_text(f'<a href="{server}/ok">a</a>\r\n<a href="{server}/absent">b</a>\r\n'
                    f'<img src="{server}/absent">\r\n<a href="../index.html">local</a> <a href="mailto:a@b.fr">m</a>\r\n'
                    '<a href="//exemple.invalid/x">protocole implicite</a>\r\n', encoding="utf-8", newline="")
    asked = []

    def check(url):
        asked.append(url)
        return external.link_error(url) if url.startswith(server) else "site introuvable"

    problems = external.check_external(site, ["page/liens.html"], check)
    assert sorted(asked) == sorted({f"{server}/ok", f"{server}/absent", "https://exemple.invalid/x"})  # Une fois chacune
    assert [(p["line"], p["message"]) for p in problems] == [
        (2, f"Lien externe en erreur, page introuvable (404) : {server}/absent"),
        (3, f"Lien externe en erreur, page introuvable (404) : {server}/absent"),
        (5, "Lien externe en erreur, site introuvable : https://exemple.invalid/x")]


def test_api_external_only_on_demand(site_client, git_site, monkeypatch):
    (git_site / "page" / "liens.html").write_text('<a href="https://exemple.invalid/">x</a>', encoding="utf-8")
    calls = []
    monkeypatch.setattr(external, "link_error",
                        lambda url: calls.append(url) or ("site introuvable" if "invalid" in url else None))
    assert not any("externe" in p["message"] for p in site_client.get("/api/checks?scope=all").get_json()["problems"])
    assert calls == []  # Sans la case cochée : pas de réseau
    problems = site_client.get("/api/checks?scope=all&external=1").get_json()["problems"]
    assert [p["page"] for p in problems if "externe" in p["message"]] == ["page/liens.html"]
