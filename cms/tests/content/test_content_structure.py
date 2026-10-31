#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de content : dupliquer ou supprimer un élément de liste ou une ligne de tableau, images éditables"""

import pytest

from content.html_manager import HTMLManager
from content.hybrid_saver import HybridSaver
from content.structure import duplicate, remove, repeatable

LIST = """<ul>
    <li class="editable" id="photo">Photo d'identité</li>
    <li><strong class="editable">Copie</strong> de la JDC</li>
</ul>
<table>
    <tr><td class="editable" id="prix">70€</td><td><p class="editable">Détail</p></td></tr>
    <tr><th class="editable">Code</th><td>30€</td></tr>
</table>
""".replace("\n", "\r\n")


def test_repeatable():
    # li éditable, élément dans un li, cellule éditable, paragraphe dans une cellule (pas toute la ligne), th
    assert repeatable(LIST) == ["li", "li", "tr", None, "tr"]


def test_duplicate_list_item_on_its_own_line():
    content, focus = duplicate(LIST, 0)
    assert '<li class="editable" id="photo">Photo d\'identité</li>\r\n    <li class="editable" id="photo-2">Photo' \
           " d'identité</li>\r\n" in content
    assert focus == 1 and repeatable(content)[:3] == ["li", "li", "li"]
    # Le reste du fichier est recopié tel quel
    assert content.replace("\r\n    <li class=\"editable\" id=\"photo-2\">Photo d'identité</li>", "", 1) == LIST


def test_duplicate_gives_unique_ids():
    once, _ = duplicate(LIST, 0)
    twice, _ = duplicate(once, 0)
    assert 'id="photo-3"' in twice and twice.count('id="photo-2"') == 1


def test_duplicate_from_an_element_inside_a_list_item():
    content, focus = duplicate(LIST, 1)
    assert content.count("de la JDC</li>") == 2 and focus == 2


def test_duplicate_table_row():
    content, focus = duplicate(LIST, 2)
    assert content.count("70€") == 2 and 'id="prix-2"' in content and focus == 4
    assert content.count("<tr>") == 3


def test_duplicate_inline_items():
    content, _ = duplicate('<ul><li class="editable">a</li><li class="editable">b</li></ul>', 1)
    assert content == '<ul><li class="editable">a</li><li class="editable">b</li> <li class="editable">b</li></ul>'


def test_remove_list_item_and_its_line():
    content = remove(LIST, 0)
    assert content == LIST.replace("\r\n    <li class=\"editable\" id=\"photo\">Photo d'identité</li>", "")


def test_remove_table_row():
    assert "Code" not in remove(LIST, 4) and "70€" in remove(LIST, 4)


def test_last_item_cannot_be_removed():
    single = remove(LIST, 0)
    with pytest.raises(ValueError, match="dernier élément de la liste"):
        remove(single, 0)
    with pytest.raises(ValueError, match="dernière ligne du tableau"):
        remove('<table><tr><td class="editable">x</td></tr></table>', 0)


@pytest.mark.parametrize("index, message", [(3, "ni dans une liste ni une cellule"), (9, "introuvable"),
                                            (-1, "introuvable")])
def test_structure_errors(index, message):
    with pytest.raises(ValueError, match=message):
        duplicate(LIST, index)


# ======= Images éditables =======

IMAGE = '<p>Équipe</p>\r\n<img class="editable" alt="Candice" src="../images/a.png" />\r\n'


def test_image_value_is_its_src(logger):
    element = HTMLManager(logger).extract_editable_elements(IMAGE)["elements"][0]
    assert element["is_image"] and not element["is_iframe"] and element["editable_value"] == "../images/a.png"


def test_image_src_is_saved():
    assert HybridSaver(IMAGE, {0: "../images/a.png"}).apply() == (IMAGE, 0)
    content, changed = HybridSaver(IMAGE, {0: "../images/b.webp"}).apply()
    assert changed == 1 and content == IMAGE.replace("a.png", "b.webp")


# ======= Version publiée associée par le contenu =======

def test_published_versions_follow_the_content():
    from content.published import align, published_versions
    published = [{"tag": "li", "html": h, "value": h} for h in ("a", "b", "c")]
    current = [{"tag": "li", "html": h, "value": h} for h in ("a", "b", "b", "c modifié")]
    # La copie de b est nouvelle ; c (modifié) garde sa version publiée malgré le décalage
    assert published_versions(current, published) == [("a", "a"), ("b", "b"), (None, None), ("c", "c")]
    assert align(["a", "b", "c"], ["a", "c"]) == [0, 2]  # b supprimé
    assert align([], ["x"]) == [None]


def test_alignment_of_a_changed_block():
    from content.published import align
    # Publié [c, d] ; actuel [copie de b, c modifié, x] : c modifié retrouve c, d devient x (même position relative)
    assert align(["b", "c", "d"], ["b", "b", "c!", "d?"]) == [0, None, 1, 2]
    assert align(["b", "zzz", "ccc"], ["b", "ccc!"]) == [0, 2]  # zzz supprimé, ccc modifié
