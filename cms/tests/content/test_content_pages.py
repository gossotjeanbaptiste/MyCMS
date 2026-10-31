#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de content : pages du site, extraction, extraits de code, gras du CSS, catégories"""

import pytest

from content.pages import css_weights
from content.pages.categories import editable_categories
from content.pages.css_weights import bold_info
from content.html.html_manager import HTMLManager
from content.pages.page_finder import find_html_pages
from site_builder import PAGES, read


@pytest.fixture
def html(logger):
    return HTMLManager(logger)


def test_pages_are_found_index_first_hidden_folders_skipped(site):
    assert find_html_pages(site) == PAGES


def test_extract_editable_elements(html, site):
    result = html.extract_editable_elements(read(site / "index.html"))
    elements = result["elements"]
    assert result["success"] and result["count"] == 8
    assert elements[1] == {**elements[1], "tag": "h1", "id": "titre", "editable_value": "Bienvenue à l'auto-école"}
    assert elements[5]["is_iframe"] and elements[5]["editable_value"] == "https://www.example.com/carte"


def test_page_without_editable_elements(html):
    result = html.extract_editable_elements("<p>rien</p>")
    assert not result["success"] and "Aucun élément éditable" in result["error"]


def test_apply_editable_html_reports_errors(html, site):
    content = read(site / "index.html")
    assert html.apply_editable_html(content, {1: "Titre"})["changed"] == 1
    result = html.apply_editable_html(content, {3: "verrou supprimé"})
    assert not result["success"] and "supprimé" in result["error"]


def test_write_file_keeps_crlf(html, tmp_path):
    target = tmp_path / "page.html"
    assert html.write_file(target, "a\r\nb")["success"]
    assert target.read_bytes() == b"a\r\nb"
    assert not html.write_file(tmp_path / "absent" / "page.html", "x")["success"]


def test_editable_snippet(html, site):
    content = read(site / "index.html")
    snippet = html.editable_snippet(content, 1, context=2)
    assert snippet["start_line"] == snippet["end_line"] == 14
    assert snippet["first_line"] == 12 and len(snippet["lines"]) == 5
    assert "Bienvenue" in snippet["lines"][2] and not snippet["lines"][2].endswith("\r")
    assert html.editable_snippet(content, 42) is None


# ======= Gras d'après le CSS du site =======

def test_bold_from_site_css(site):
    flags, selectors = bold_info(site, "index.html", read(site / "index.html"))
    # Titre sans gras (pas de gras par défaut sur les titres) ; .highlight en gras par une variable CSS
    assert flags == [False, False, False, False, False, False, True, False]
    assert ".highlight" in selectors and ".titre-gras" in selectors  # @import suivi
    assert "a" not in selectors  # a:hover : état, pas le texte affiché normalement


def test_strong_is_bold_by_default(site):
    flags, _ = bold_info(site, "page/formations.html", read(site / "page/formations.html"))
    assert flags[1] is True and flags[0] is False


def test_inline_style_and_specificity(tmp_path):
    content = """<style>p { font-weight: 700 } #a { font-weight: 400 } .x { font-weight: 900 }</style>
    <p class="editable" id="a">a</p><p class="editable x">b</p>
    <p class="editable" style="font-weight: normal">c</p><div style="font-weight:bold"><span class="editable">d</span></div>"""
    flags, _ = bold_info(tmp_path, "page.html", content)
    assert flags == [False, True, False, True]


@pytest.mark.parametrize("value, expected", [
    ("bold", True), ("bolder", True), ("600", True), ("500", False), ("normal", False), ("lighter", False),
    ("700 !important", True), ("inherit", None), ("var(--w)", True), ("var(--x, bold)", True), ("var(--x)", None),
])
def test_font_weight_values(value, expected):
    assert css_weights._is_bold(value, {"--w": "800"}) is expected


def test_css_outside_the_site_is_ignored(tmp_path):
    (tmp_path / "dehors.css").write_text("p { font-weight: bold }", encoding="utf-8")
    site = tmp_path / "site"
    site.mkdir()
    content = '<link rel="stylesheet" href="../dehors.css"><link rel="stylesheet" href="https://cdn/x.css"><p class="editable">a</p>'
    assert bold_info(site, "index.html", content)[0] == [False]


# ======= Catégories =======

def categories(site, page):
    return editable_categories(read(site / page))


def test_categories_landmarks_and_headings(site):
    title = "Bienvenue à l'auto-école"
    # Le lien « Haut de page » vise <body id="top"> : il ne nomme pas de bloc
    assert categories(site, "index.html") == ["Menu"] + [title] * 6 + ["Pied de page"]


def test_categories_select_options_tables_and_captions(site):
    assert categories(site, "page/formations.html") == [
        "Permis B - Traditionnel", "Permis B - Traditionnel", "Permis Moto A2",
        "Horaires", "Horaires",  # Plusieurs <th> : en-têtes de colonnes, pas un titre
        "Tarifs"]


def test_categories_from_summary_links(site):
    assert categories(site, "page/financement.html") == ["Permis à 1€ / jour"] * 3 + ["CFA"] * 3


def test_categories_sub_sections_and_declared(site):
    assert categories(site, "page/mentions.html") == [
        "Mentions légales", "1. Éditeur du site", "1. Éditeur du site", "2. Hébergeur", "2. Hébergeur", "Contact"]


def test_subtitles_and_long_titles_are_not_merged():
    long_title = "Notre auto-école vous propose cette opportunité ouverte à " + "x" * 10
    content = f"""<div><h2 class="editable">A</h2><h3 class="editable">{long_title}tous</h3><p class="editable">1</p></div>
    <div><h2 class="editable">B</h2><h3 class="editable">{long_title}apprentis</h3><p class="editable">2</p></div>
    <h3>{long_title}tous</h3><p class="editable">3</p><h3>{long_title}apprentis</h3><p class="editable">4</p>"""
    result = editable_categories(content)
    assert result[:6] == ["A", "A", "A", "B", "B", "B"]
    assert result[6] != result[7]


def test_category_without_heading_is_other():
    assert editable_categories('<p class="editable">a</p>') == ["Autres"]
