// Tests des filtres de catégories et de la recherche, sur des cartes construites comme dans l'éditeur

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { renderElements } from "../static/scripts/editor/cards.js";
import { renderCategories, revealCard, selectCategory, updateCategoryDirty } from "../static/scripts/editor/categories.js";
import { applySearch, clearSearch } from "../static/scripts/editor/search.js";
import { state } from "../static/scripts/core/state.js";

const $ = (id) => document.getElementById(id);
const ELEMENTS = [
    ["Permis B", "Formation au permis B"], ["Permis B", "Étapes de la formation"],
    ["Moto A2", "Formation moto"], ["Moto A2", "Équipement obligatoire"], ["Tarifs", "Code : 30 €"],
].map(([category, html], index) => ({ index, tag: "p", id: null, is_iframe: false, html, value: html,
    nested: [], bold: false, category }));

const visible = () => [...document.querySelectorAll("#editable-list .field:not(.hidden)")].map((c) => Number(c.id.slice(6)));
const chips = () => [...document.querySelectorAll("#category-bar .chip")].map((c) => c.textContent);
const search = (text) => { $("search").value = text; applySearch(); };

beforeEach(() => {
    state.editor.file = "page/formations.html";
    state.editor.category = "";
    $("search").value = "";
    renderCategories(ELEMENTS);
    renderElements(ELEMENTS);
    applySearch();
});

test("un filtre par catégorie, dans l'ordre de la page, avec le nombre d'éléments", () => {
    assert.deepEqual(chips(), ["Tout5", "Permis B2", "Moto A22", "Tarifs1"]);
    assert.ok(!$("category-bar").classList.contains("hidden"));
    assert.equal($("category-bar").querySelector('[aria-pressed="true"]').dataset.category, "");
});

test("un intertitre à chaque changement de catégorie", () => {
    const titles = [...document.querySelectorAll("#editable-list .category-title")].map((t) => t.textContent);
    assert.deepEqual(titles, ["Permis B", "Moto A2", "Tarifs"]);
    assert.equal($("field-2").dataset.category, "Moto A2");
});

test("choisir une catégorie n'affiche que ses éléments et son intertitre", () => {
    selectCategory("Moto A2");
    assert.deepEqual(visible(), [2, 3]);
    const shownTitles = [...document.querySelectorAll(".category-title:not(.hidden)")].map((t) => t.textContent);
    assert.deepEqual(shownTitles, ["Moto A2"]);
    assert.equal($("category-bar").querySelector('[aria-pressed="true"]').dataset.category, "Moto A2");
    selectCategory("");
    assert.deepEqual(visible(), [0, 1, 2, 3, 4]);
});

test("la recherche ignore accents et majuscules", () => {
    search("equipement");
    assert.deepEqual(visible(), [3]);
    assert.equal($("search-count").textContent, "1 élément");
    search("FORMATION");
    assert.deepEqual(visible(), [0, 1, 2]);
});

test("la recherche est limitée à la catégorie choisie", () => {
    selectCategory("Moto A2");
    search("formation");
    assert.deepEqual(visible(), [2]);
    search("code");
    assert.equal($("search-count").textContent, "Aucun résultat");
    assert.equal($("search-empty").textContent, "Aucun élément dans « Moto A2 » ne contient « code »");
    clearSearch();
    assert.equal($("search-empty"), null);
    assert.deepEqual(visible(), [2, 3]);
});

test("point sur les filtres qui ont des modifications non sauvegardées", () => {
    $("field-4").classList.add("dirty");
    updateCategoryDirty();
    const dirty = [...document.querySelectorAll("#category-bar .chip.dirty")].map((c) => c.dataset.category);
    assert.deepEqual(dirty, ["", "Tarifs"]);
});

test("une carte masquée est réaffichée quand on y va depuis l'aperçu", () => {
    selectCategory("Tarifs");
    search("zzz");
    revealCard($("field-0"));
    assert.equal(state.editor.category, "");
    assert.equal($("search").value, "");
    assert.ok(!$("field-0").classList.contains("hidden"));
    revealCard(null);  // Sans carte : rien ne se passe
});

test("le filtre est gardé au rechargement de la page, oublié s'il n'existe plus", () => {
    selectCategory("Tarifs");
    renderCategories(ELEMENTS);
    assert.equal(state.editor.category, "Tarifs");
    renderCategories(ELEMENTS.slice(0, 3));
    assert.equal(state.editor.category, "");
});

test("une seule catégorie : pas de barre de filtres", () => {
    renderCategories(ELEMENTS.slice(0, 2));
    assert.ok($("category-bar").classList.contains("hidden"));
    assert.deepEqual(chips(), []);
});
