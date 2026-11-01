// Tests du brouillon de l'éditeur : modifications non sauvegardées gardées dans le navigateur

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { clearDraft, initDraft, offerDraft, scheduleDraft } from "../static/scripts/editor/draft.js";
import { state } from "../static/scripts/core/state.js";

const editor = state.editor;
const KEY = "mycms-draft:page/tarifs.html";

// Deux champs : un texte enrichi et l'adresse d'une image ; inputs : index des champs qui ont reçu « input »
function page(hash = "h1") {
    editor.file = "page/tarifs.html";
    editor.hash = hash;
    const inputs = [];
    editor.fields = new Map([[0, "rich"], [1, "src"]].map(([index, kind]) => {
        const card = document.createElement("div");
        card.className = "field";
        const el = document.createElement(kind === "rich" ? "div" : "input");
        if (kind === "rich") el.innerHTML = "Tarif : <b>70 €</b>";
        else el.value = "../images/a.png";
        el.addEventListener("input", () => inputs.push(index));
        card.append(el);
        return [index, { el, kind, card }];
    }));
    return inputs;
}

function written() {
    return JSON.parse(localStorage.getItem(KEY) || "null");
}

beforeEach(() => {
    localStorage.clear();
    globalThis.confirm = () => true;
    document.getElementById("toasts").replaceChildren();
});

test("seuls les champs modifiés sont gardés, au moment où l'onglet se ferme", () => {
    page();
    initDraft();
    const rich = editor.fields.get(0);
    rich.el.innerHTML = "Tarif : <b>75 €</b>";
    rich.card.classList.add("dirty");
    scheduleDraft();
    assert.equal(written(), null); // Pas d'écriture à chaque touche
    window.dispatchEvent(new Event("pagehide"));
    assert.deepEqual(written().values, { 0: "Tarif : <b>75 €</b>" });
    assert.equal(written().hash, "h1");
    // Plus rien de modifié : le brouillon disparaît
    rich.card.classList.remove("dirty");
    window.dispatchEvent(new Event("pagehide"));
    assert.equal(written(), null);
});

test("le brouillon retrouvé est remis, comme une saisie", () => {
    localStorage.setItem(KEY, JSON.stringify({ hash: "h1", saved: Date.now(), values: { 0: "Nouveau <b>tarif</b>", 1: "../images/b.png" } }));
    const inputs = page("h1");
    offerDraft();
    assert.equal(editor.fields.get(0).el.innerHTML, "Nouveau <b>tarif</b>");
    assert.equal(editor.fields.get(1).el.value, "../images/b.png");
    assert.deepEqual(inputs, [0, 1]);
    assert.notEqual(written(), null); // Gardé jusqu'à la sauvegarde
});

test("brouillon refusé : il est effacé", () => {
    localStorage.setItem(KEY, JSON.stringify({ hash: "h1", saved: Date.now(), values: { 0: "Autre" } }));
    const inputs = page("h1");
    globalThis.confirm = () => false;
    offerDraft();
    assert.equal(editor.fields.get(0).el.innerHTML, "Tarif : <b>70 €</b>");
    assert.deepEqual(inputs, []);
    assert.equal(written(), null);
});

test("page changée depuis : le brouillon n'est pas remis", () => {
    localStorage.setItem(KEY, JSON.stringify({ hash: "ancien", saved: Date.now(), values: { 0: "Autre" } }));
    let asked = false;
    globalThis.confirm = () => (asked = true);
    const inputs = page("h2");
    offerDraft();
    assert.ok(!asked && inputs.length === 0 && written() === null);
    assert.match(document.getElementById("toasts").textContent, /a changé depuis/);
});

test("clearDraft après une sauvegarde", () => {
    localStorage.setItem(KEY, "{}");
    page();
    clearDraft();
    assert.equal(written(), null);
});
