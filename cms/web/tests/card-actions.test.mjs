// Tests des actions des cartes (v2.1.2) : version en ligne, dupliquer / supprimer, champ d'image

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";
import { renderElements } from "../static/scripts/editor/cards.js";
import { initEditorInput } from "../static/scripts/editor/input.js";
import { applySearch } from "../static/scripts/editor/search.js";
import { initStructure } from "../static/scripts/editor/structure.js";
import { state } from "../static/scripts/core/state.js";

const $ = (id) => document.getElementById(id);
const realFetch = globalThis.fetch;
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

const ELEMENTS = [
    { tag: "li", html: "Photo d'identité modifiée", published_html: "Photo d'identité", repeat: "li" },
    { tag: "td", html: "70€", published_html: "70€", repeat: "tr" },
    { tag: "p", html: "Paragraphe", published_html: "Paragraphe", repeat: null },
    { tag: "img", html: "", value: "../images/voiture.png", published_value: "../images/voiture.png", is_image: true },
].map((elem, index) => ({ index, id: null, is_iframe: false, is_image: false, value: elem.html, nested: [],
    bold: false, category: "Tarifs", published_value: elem.html, ...elem }));

const actions = (index) => [...$(`field-${index}`).querySelectorAll(".card-actions button:not(.hidden)")]
    .map((b) => b.dataset.action);

initEditorInput();
initStructure();

beforeEach(() => {
    state.editor.file = "page/tarifs.html";
    state.editor.publishedKnown = true;
    state.editor.category = "";
    $("search").value = "";
    renderElements(ELEMENTS);
});

afterEach(() => { globalThis.fetch = realFetch; });

test("dupliquer / supprimer seulement pour un élément de liste ou une cellule", () => {
    assert.deepEqual(actions(0), ["restore", "duplicate", "delete"]);  // Modifié depuis le dernier push
    assert.deepEqual(actions(1), ["duplicate", "delete"]);
    assert.deepEqual(actions(2), []);
    assert.equal($("field-1").querySelector(".card-actions").dataset.what, "la ligne du tableau");
});

test("le texte des boutons n'est pas cherché", () => {
    $("search").value = "supprimer";
    applySearch();
    assert.equal(document.querySelectorAll("#editable-list .field:not(.hidden)").length, 0);
});

test("« Version en ligne » remet le contenu publié et la carte devient modifiée", () => {
    $("field-0").querySelector('[data-action="restore"]').click();
    const field = state.editor.fields.get(0);
    assert.equal(field.el.innerHTML, "Photo d'identité");
    assert.ok($("field-0").classList.contains("dirty"));
    assert.ok($("field-0").querySelector('[data-action="restore"]').classList.contains("hidden"));
    assert.match(document.querySelector("#toasts .toast:last-child").textContent, /Version en ligne remise/);
});

test("« Version en ligne » qui annule seulement la saisie : rien à sauvegarder", () => {
    // Fichier enregistré identique à la version en ligne ; seule la saisie l'avait changé
    const field = state.editor.fields.get(1);
    field.el.innerHTML = "75€";
    field.el.dispatchEvent(new window.Event("input", { bubbles: true }));
    $("field-1").querySelector('[data-action="restore"]').click();
    assert.equal(field.el.innerHTML, "70€");
    assert.ok(!$("field-1").classList.contains("dirty"));
    assert.equal(document.querySelector("#toasts .toast:last-child").textContent,
        "Texte revenu à la version en ligne : rien à sauvegarder.");
});

test("supprimer demande une confirmation", () => {
    let called = false;
    globalThis.fetch = async () => { called = true; return Response.json({}); };
    globalThis.confirm = () => false;
    $("field-1").querySelector('[data-action="delete"]').click();
    assert.equal(called, false);
});

test("carte d'une image : vignette du site et adresse modifiable", () => {
    const card = $("field-3");
    const input = state.editor.fields.get(3).el;
    const thumbnail = card.querySelector("img");
    assert.equal(input.value, "../images/voiture.png");
    assert.equal(thumbnail.getAttribute("src"), "/api/site-image?page=page%2Ftarifs.html&src=..%2Fimages%2Fvoiture.png");
    input.value = "../images/autre.png";
    input.dispatchEvent(new window.Event("input", { bubbles: true }));
    assert.match(thumbnail.getAttribute("src"), /autre\.png$/);
    assert.ok(card.classList.contains("dirty"));
});

test("choisir une image l'envoie au serveur et met sa nouvelle adresse", async () => {
    let sent;
    globalThis.fetch = async (url, options) => {
        sent = { url, options };
        return Response.json({ success: true, src: "../images/photo.png", path: "images/photo.png" });
    };
    const picker = $("field-3").querySelector('input[type="file"]');
    Object.defineProperty(picker, "files", { value: [new File(["png"], "photo.png", { type: "image/png" })] });
    picker.dispatchEvent(new window.Event("change"));
    await tick();
    await tick();
    assert.equal(sent.url, "/api/images");
    assert.equal(sent.options.body.get("page"), "page/tarifs.html");
    assert.equal(sent.options.headers["Content-Type"], undefined);  // Le navigateur fixe l'en-tête multipart
    assert.equal(state.editor.fields.get(3).el.value, "../images/photo.png");
    assert.ok($("field-3").classList.contains("dirty"));
});

test("envoi refusé : le message du serveur est affiché", async () => {
    globalThis.fetch = async () => Response.json({ success: false, error: "Format non accepté" }, { status: 400 });
    const picker = $("field-3").querySelector('input[type="file"]');
    Object.defineProperty(picker, "files", { value: [new File(["x"], "a.svg")] });
    picker.dispatchEvent(new window.Event("change"));
    await tick();
    await tick();
    assert.equal(document.querySelector("#toasts .toast.error:last-child").textContent, "Format non accepté");
    assert.equal(state.editor.fields.get(3).el.value, "../images/voiture.png");
});
