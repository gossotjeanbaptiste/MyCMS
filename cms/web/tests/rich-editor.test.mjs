// Tests de l'éditeur de texte enrichi : HTML source -> éditeur -> HTML envoyé au serveur

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";
import { applySiteBoldRules, buildRichEditor, fieldValue, serializeRich, VOID_TAGS } from "../static/scripts/editor/rich-editor.js";

const element = (html, extra = {}) => ({ index: 3, tag: "p", html, nested: [], bold: false, ...extra });

test("le contenu revient tel qu'il est entré", () => {
    for (const html of ["Texte simple", "Le <strong>permis</strong> pour <em>tous</em>", "Un<br>deux",
        '<a href="https://exemple.fr" target="_blank">lien</a>', "a &amp; b &lt; c"]) {
        assert.equal(serializeRich(buildRichEditor(element(html)).editor), html);
    }
});

test("l'éditeur porte l'index, la balise et le gras calculé par le serveur", () => {
    const { editor, locks } = buildRichEditor(element("x", { bold: true }));
    assert.equal(editor.className, "rich");
    assert.equal(editor.dataset.index, "3");
    assert.equal(editor.dataset.tag, "p");
    assert.equal(editor.style.fontWeight, "700");
    assert.equal(locks, 0);
    assert.equal(buildRichEditor(element("x")).editor.style.fontWeight, "400");
});

test("les attributs on* ne s'exécutent pas dans l'éditeur, mais sont renvoyés", () => {
    const html = '<span onclick="alert(1)" class="a">clic</span>';
    const { editor } = buildRichEditor(element(html));
    const span = editor.querySelector("span");
    assert.equal(span.getAttribute("onclick"), null);
    assert.equal(span.getAttribute("data-mycms-onclick"), "alert(1)");
    // L'attribut revient en fin de balise : le serveur compare les attributs sans tenir compte de l'ordre
    assert.equal(serializeRich(editor), '<span class="a" onclick="alert(1)">clic</span>');
});

test("un élément éditable imbriqué devient un bloc verrouillé, puis un marqueur", () => {
    const html = 'Avant <span class="editable" id="imbrique">un texte imbriqué</span> après';
    const { editor, locks } = buildRichEditor(element(html, { nested: [4] }));
    const lock = editor.querySelector(".lock");
    assert.equal(locks, 1);
    assert.equal(lock.dataset.locked, "4");
    assert.equal(lock.contentEditable, "false");
    assert.match(lock.textContent, /un texte imbriqué/);
    assert.equal(serializeRich(editor), 'Avant <mycms-lock data-index="4"></mycms-lock> après');
});

test("le libellé d'un long bloc verrouillé est raccourci", () => {
    const long = "x".repeat(60);
    const { editor } = buildRichEditor(element(`<b class="editable">${long}</b>`, { nested: [9] }));
    assert.equal(editor.querySelector(".lock").textContent, "x".repeat(40) + "…");
});

test("structure non reconnue : pas d'éditeur", () => {
    assert.equal(buildRichEditor(element('<span class="editable">a</span>', { nested: [] })), null);
});

test("seuls les sélecteurs sûrs du CSS du site sont appliqués", () => {
    applySiteBoldRules([".highlight", "strong", "a:hover", "div > p", "x}body{color:red"]);
    assert.equal(document.getElementById("site-bold-rules").textContent,
        ".rich :is(.highlight, strong) { font-weight: 700; }");
    applySiteBoldRules([]);
    assert.equal(document.getElementById("site-bold-rules").textContent, "");
    assert.equal(document.querySelectorAll("#site-bold-rules").length, 1);
});

test("valeur d'un champ : texte enrichi ou src d'une iframe", () => {
    const { editor } = buildRichEditor(element("<b>x</b>"));
    assert.equal(fieldValue({ kind: "rich", el: editor }), "<b>x</b>");
    assert.equal(fieldValue({ kind: "src", el: { value: "https://carte" } }), "https://carte");
    assert.ok(VOID_TAGS.has("img") && !VOID_TAGS.has("p"));
});
