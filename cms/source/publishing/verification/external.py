#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liens externes, vérifiés sur demande (« Vérifier le site ») : un partenaire qui a changé d'adresse,
un document retiré d'un autre site. Chaque adresse http(s) n'est demandée qu'une fois, en parallèle.

Seules les erreurs sûres sont signalées : page introuvable (404, 410), site introuvable ou qui ne répond pas.
Les sites qui refusent les robots (401, 403, 429…) sont considérés comme bons : un visiteur y accède.
"""

import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from content.html.html_tree import parse
from publishing.verification.checks import LINK_ATTRIBUTES, _problem, _walk

TIMEOUT = 10
WORKERS = 8
GONE = {404: "page introuvable (404)", 410: "page supprimée (410)"}
# Méthode HEAD refusée par certains serveurs : on redemande la page
RETRY_WITH_GET = {400, 403, 405, 501}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MyCMS link check)", "Accept": "*/*"}


def _absolute(url):
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    return url if url.lower().startswith(("http://", "https://")) else None


def collect(repo_path, pages):
    """Adresses externes des pages : {adresse: [(page, contenu, nœud)]}, pour situer chaque problème"""
    found = {}
    for page in pages:
        try:
            with open(Path(repo_path) / page, encoding="utf-8", newline="") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        for node in _walk(parse(content)[0]):
            attribute = LINK_ATTRIBUTES.get(node.tag)
            url = _absolute(node.attr(attribute) or "") if attribute else None
            if url:
                found.setdefault(url, []).append((page, content, node))
    return found


def _request(url, method):
    request = urllib.request.Request(url, method=method, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT):
        pass


def link_error(url):
    """Ce qui ne va pas avec une adresse externe, ou None si un visiteur peut l'ouvrir"""
    try:
        try:
            _request(url, "HEAD")
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_WITH_GET:
                raise
            _request(url, "GET")
    except urllib.error.HTTPError as error:
        return GONE.get(error.code)
    except urllib.error.URLError as error:
        if isinstance(error.reason, socket.gaierror):
            return "site introuvable (l'adresse n'existe plus ?)"
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            return "le site ne répond pas"
        return f"site injoignable ({error.reason})"
    except (TimeoutError, socket.timeout):
        return "le site ne répond pas"
    except (OSError, ValueError) as error:
        return f"adresse inutilisable ({error})"
    return None


def check_external(repo_path, pages, check=None):
    """Problèmes des liens externes : [{page, line, message}], comme check_pages"""
    found = collect(repo_path, pages)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        errors = dict(zip(found, pool.map(check or link_error, found)))
    problems = [_problem(page, content, node, f"Lien externe en erreur, {errors[url]} : {url}")
                for url, places in found.items() if errors[url] for page, content, node in places]
    return sorted(problems, key=lambda p: (p["page"], p["line"]))
