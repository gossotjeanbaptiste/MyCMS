#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Site de test : quelques pages qui reprennent les cas du site de l'auto-école
(tableaux affichés par une liste déroulante, sommaire, éléments imbriqués, iframe, gras du CSS).
Écrit en CRLF, comme le vrai site.
"""

from pathlib import Path

INDEX = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Accueil</title>
    <link rel="stylesheet" href="style/style.css">
</head>
<body id="top">
    <header class="main-header">
        <nav><a href="index.html" class="editable">Accueil</a></nav>
    </header>
    <main>
        <section>
            <h1 class="editable" id="titre">Bienvenue à l'auto-école</h1>
            <p class="editable" id="intro">Le <strong>permis</strong> pour tous, avec&nbsp;des moniteurs <em>diplômés</em>.</p>
            <div class="editable" id="bloc">Un bloc avec un texte <span class="editable" id="imbrique">imbriqué</span> dedans.</div>
            <iframe class="editable" src="https://www.example.com/carte" title="Carte"></iframe>
            <p class="highlight editable" id="promo" onclick="alert(1)">Offre spéciale</p>
        </section>
        <a href="#top">Haut de page</a>
    </main>
    <footer><p class="editable" id="copyright">© 2026 Auto-école</p></footer>
</body>
</html>
"""

FORMATIONS = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Formations</title>
    <link rel="stylesheet" href="../style/style.css">
</head>
<body>
    <main>
        <select id="formation-select">
            <option value="b-traditionnel">Permis B - Traditionnel</option>
            <option value="moto-a2">Permis Moto A2</option>
        </select>
        <table id="table-b-traditionnel">
            <thead><tr><th>PERMIS B</th></tr></thead>
            <tbody>
                <tr><td class="editable" id="desc-b">Formation au permis B.</td></tr>
                <tr><td><strong class="editable">Étapes :</strong></td></tr>
            </tbody>
        </table>
        <table id="table-moto-a2">
            <thead><tr><th>MOTO A2</th></tr></thead>
            <tbody><tr><td class="editable">Formation moto.</td></tr></tbody>
        </table>
        <h2>Horaires</h2>
        <table class="horaires">
            <thead><tr><th>Jour</th><th>Horaires</th></tr></thead>
            <tbody><tr><td class="editable">Lundi</td><td class="editable">9h - 12h</td></tr></tbody>
        </table>
        <table>
            <caption>Tarifs</caption>
            <tbody><tr><td class="editable">Code : 30 €</td></tr></tbody>
        </table>
    </main>
</body>
</html>
"""

FINANCEMENT = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>Financement</title></head>
<body>
    <nav class="quick-nav"><a href="#permis-1euro">Permis à 1€ / jour</a> <a href="#cfa">CFA</a></nav>
    <main>
        <div id="permis-1euro">
            <h2 class="editable">Permis à 1€/jour</h2>
            <h3 class="editable">Notre auto-école vous propose cette opportunité ouverte à tous</h3>
            <p class="editable">Un prêt à taux zéro.</p>
        </div>
        <div id="cfa">
            <h2 class="editable">CFA</h2>
            <h3 class="editable">Notre auto-école vous propose cette opportunité ouverte aux apprentis</h3>
            <p class="editable">Une aide de 500 €.</p>
        </div>
    </main>
</body>
</html>
"""

MENTIONS = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="robots" content="noindex, follow">
    <title>Mentions légales</title>
</head>
<body>
    <main>
        <section>
            <h2 class="editable">Mentions légales</h2>
            <div><h3 class="editable">1. Éditeur du site</h3><p class="editable">Rout'Art</p></div>
            <div><h3 class="editable">2. Hébergeur</h3><p class="editable">GitHub</p></div>
            <div data-category="Contact"><p class="editable">contact@exemple.fr</p></div>
        </section>
    </main>
</body>
</html>
"""

SECRET = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Privé</title></head>
<body><p class="editable">Page privée</p></body></html>
"""

STYLE = """@import "base.css";
:root { --gras: 700; }
.highlight { font-weight: var(--gras); }
h1 { font-weight: normal; }
a:hover { font-weight: bold; }
"""

BASE_CSS = """/* Feuille importée */
.titre-gras { font-weight: bold; }
"""

ROBOTS = """User-agent: *
Disallow: /page/prive/
Sitemap: https://exemple.github.io/sitemap.xml
"""

FILES = {
    "index.html": INDEX,
    "page/formations.html": FORMATIONS,
    "page/financement.html": FINANCEMENT,
    "page/mentions.html": MENTIONS,
    "page/prive/secret.html": SECRET,
    "style/style.css": STYLE,
    "style/base.css": BASE_CSS,
    "robots.txt": ROBOTS,
    # Jamais parcourus par la recherche des pages
    "node_modules/paquet/doc.html": SECRET,
    ".cache/vieux.html": SECRET,
}

PAGES = ["index.html", "page/financement.html", "page/formations.html", "page/mentions.html",
         "page/prive/secret.html"]


def build_site(path):
    """Écrire le site de test dans path (fins de ligne CRLF) et retourner path"""
    path = Path(path)
    for relative, text in FILES.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    return path


def read(path):
    """Contenu exact d'un fichier (sans conversion des fins de ligne)"""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()
