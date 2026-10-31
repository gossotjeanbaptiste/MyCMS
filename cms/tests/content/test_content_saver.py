#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de content : arbre HTML et sauvegarde hybride (fidélité à l'octet près)"""

import pytest

from content.html.html_tree import editable_sources, norm, parse
from content.html.hybrid_saver import HybridSaver, set_attribute
from site_builder import read

LOCK = '<mycms-lock data-index="4"></mycms-lock>'


@pytest.fixture
def index(site):
    return read(site / "index.html")


def save(content, values):
    return HybridSaver(content, values).apply()


def sources(content):
    return [source["html"] for source in editable_sources(content)]


# ======= Arbre HTML =======

def test_tree_keeps_exact_positions(index):
    root, editables = parse(index)
    assert len(editables) == 8
    intro = editables[2]
    assert index[intro.start:intro.end].startswith('<p class="editable" id="intro">Le <strong>')
    assert index[intro.inner_start:intro.inner_end].endswith("<em>diplômés</em>.")
    assert [e.editable_index for e in editables] == list(range(8))
    assert root.end == len(index)


def test_editable_sources_list_nested_elements(index):
    result = editable_sources(index)
    assert result[3]["nested"] == [4] and result[2]["nested"] == []
    assert result[4]["html"] == "imbriqué"


def test_unclosed_tags_and_comments_are_handled():
    content = "<div class='editable'><p>un<p>deux</div><!-- commentaire --><span class=\"editable\">x</span>"
    _, editables = parse(content)
    assert len(editables) == 2 and content[editables[1].start:editables[1].end] == '<span class="editable">x</span>'


def test_norm_converts_line_endings():
    assert norm("a\r\nb\rc") == "a\nb\nc" and norm(None) == ""


# ======= Sauvegarde : aller-retour sans modification =======

def test_no_values_leaves_file_identical(index):
    assert save(index, {}) == (index, 0)


def test_sending_back_every_element_unchanged_is_byte_identical(index):
    values = {i: html for i, html in enumerate(sources(index)) if i not in (3, 5)}
    values[3] = sources(index)[3].replace('<span class="editable" id="imbrique">imbriqué</span>', LOCK)
    values[5] = "https://www.example.com/carte"
    content, _ = save(index, values)
    assert content == index


def test_browser_rewrites_are_not_changes(index):
    """Le navigateur renvoie &nbsp; en caractère, des fins de ligne \\n et les attributs dans son propre format"""
    value = sources(index)[2].replace("&nbsp;", " ").replace("\r\n", "\n")
    assert save(index, {2: value})[0] == index


# ======= Sauvegarde : modifications =======

def test_only_the_changed_element_is_rewritten(index):
    content, changed = save(index, {1: "Bienvenue chez Rout'Art"})
    assert changed == 1
    assert '<h1 class="editable" id="titre">Bienvenue chez Rout\'Art</h1>' in content
    assert content.replace("Bienvenue chez Rout'Art", "Bienvenue à l'auto-école") == index
    assert content.count("\r\n") == index.count("\r\n")


def test_unchanged_markup_inside_a_changed_element_is_copied(index):
    value = sources(index)[2].replace("diplômés", "expérimentés")
    content, _ = save(index, {2: value})
    assert "Le <strong>permis</strong> pour tous, avec&nbsp;des moniteurs <em>expérimentés</em>." in content


@pytest.mark.parametrize("sent, written", [
    ("<b>gras</b>", "<strong>gras</strong>"),
    ("<i>penché</i>", "<em>penché</em>"),
    ('<span style="color:red">rouge</span>', "rouge"),
    ('<a href="https://exemple.fr" target="_blank">lien</a>', '<a href="https://exemple.fr">lien</a>'),
    ('<a href="javascript:alert(1)">piège</a>', "piège"),
    ('<a href=" data:text/html,x">piège</a>', "piège"),
    ("ligne 1<div>ligne 2</div>", "ligne 1<br>ligne 2"),
    ("un<br>deux", "un<br>deux"),
    ("<script>alert(1)</script>texte", "alert(1)texte"),
    ("a < b & c", "a &lt; b &amp; c"),
])
def test_new_html_is_cleaned(index, sent, written):
    content, _ = save(index, {7: sent})
    assert f'<p class="editable" id="copyright">{written}</p>' in content


def test_new_line_breaks_follow_the_file(index):
    content, _ = save(index, {7: "un\ndeux"})
    assert "un\r\ndeux" in content


def test_nested_element_is_kept_when_parent_changes(index):
    content, _ = save(index, {3: f"Texte remplacé {LOCK} fin."})
    assert '<div class="editable" id="bloc">Texte remplacé <span class="editable" id="imbrique">imbriqué</span> fin.</div>' in content


def test_parent_and_nested_element_changed_together(index):
    content, changed = save(index, {3: f"Avant {LOCK}", 4: "nouveau"})
    assert changed == 2 and '<div class="editable" id="bloc">Avant <span class="editable" id="imbrique">nouveau</span></div>' in content


def test_removing_a_nested_element_is_refused(index):
    with pytest.raises(ValueError, match=r"imbriqué \[4\] a été supprimé de l'élément \[3\]"):
        save(index, {3: "plus de verrou"})


def test_iframe_src(index):
    assert save(index, {5: "https://www.example.com/carte"}) == (index, 0)
    content, changed = save(index, {5: "https://maps.exemple.fr/?q=a&b"})
    assert changed == 1 and 'src="https://maps.exemple.fr/?q=a&amp;b"' in content


def test_event_attributes_are_kept(index):
    content, _ = save(index, {6: "Offre du mois"})
    assert '<p class="highlight editable" id="promo" onclick="alert(1)">Offre du mois</p>' in content


def test_unknown_index_is_ignored(index):
    assert save(index, {99: "x", -1: "y"}) == (index, 0)


def test_lf_file_stays_lf():
    content = '<p class="editable">a</p>\n<p class="editable">b</p>\n'
    assert save(content, {1: "x\ny"})[0] == '<p class="editable">a</p>\n<p class="editable">x\ny</p>\n'


@pytest.mark.parametrize("tag, expected", [
    ('<iframe src="a">', '<iframe src="&quot;b&quot;">'),
    ("<iframe SRC='a' title=x>", "<iframe SRC=\"&quot;b&quot;\" title=x>"),
    ('<iframe title="x">', '<iframe title="x" src="&quot;b&quot;">'),
    ("<img/>", '<img src="&quot;b&quot;"/>'),
])
def test_set_attribute(tag, expected):
    assert set_attribute(tag, "src", '"b"') == expected
