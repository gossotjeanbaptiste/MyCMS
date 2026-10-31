// Tests des marqueurs « pas encore publié » : + plus de contenu, − moins, ~ autant mais modifié

import "./setup-dom.mjs";
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { setPublished, updateAllMarkers, updateMarker } from "../static/scripts/editor/markers.js";
import { buildRichEditor } from "../static/scripts/editor/rich-editor.js";
import { state } from "../static/scripts/core/state.js";

// Carte de l'éditeur pour un élément dont la version publiée est publishedHtml
function richField(publishedHtml, currentHtml = publishedHtml) {
    const card = document.createElement("div");
    card.className = "field";
    card.innerHTML = '<span class="pub-badge hidden"></span>';
    document.getElementById("editable-list").append(card);
    const elem = { index: 0, tag: "p", html: currentHtml, nested: [], published_html: publishedHtml,
        published_value: publishedHtml };
    const field = { el: buildRichEditor(elem).editor, kind: "rich", card };
    setPublished(field, elem);
    return field;
}

const badge = (field) => field.card.querySelector(".pub-badge");

beforeEach(() => {
    state.editor.publishedKnown = true;
    document.getElementById("editable-list").replaceChildren();
});

test("aucun marqueur quand rien n'a changé", () => {
    const field = richField("Texte <b>publié</b>");
    updateMarker(field);
    assert.ok(badge(field).classList.contains("hidden"));
    assert.ok(document.getElementById("pub-legend").classList.contains("hidden"));
});

for (const [current, symbol, cls] of [["Texte plus long", "+", "pub-add"], ["Tex", "−", "pub-del"],
    ["Texta", "~", "pub-mod"]]) {
    test(`marqueur ${symbol}`, () => {
        const field = richField("Texte", current);
        updateMarker(field);
        assert.equal(badge(field).textContent, symbol);
        assert.ok(field.card.classList.contains(cls));
        assert.ok(!document.getElementById("pub-legend").classList.contains("hidden"));
    });
}

test("le marqueur disparaît quand on revient au texte publié", () => {
    const field = richField("Texte", "Autre texte");
    updateMarker(field);
    field.el.innerHTML = "Texte";
    updateMarker(field);
    assert.ok(badge(field).classList.contains("hidden"));
    assert.ok(!field.card.classList.contains("pub-add"));
});

test("élément absent de la version publiée : +", () => {
    const field = richField(null, "Nouveau");
    updateAllMarkers();
    updateMarker(field);
    assert.equal(badge(field).textContent, "+");
});

test("version publiée inconnue (pas de branche distante) : pas de marqueur", () => {
    state.editor.publishedKnown = false;
    const field = richField("Texte", "Autre texte plus long");
    updateMarker(field);
    assert.equal(field.published, undefined);
    assert.ok(badge(field).classList.contains("hidden"));
});

test("iframe : comparaison de l'adresse", () => {
    const card = document.createElement("div");
    card.innerHTML = '<span class="pub-badge hidden"></span>';
    const field = { el: { value: "https://carte/longue-adresse" }, kind: "src", card };
    setPublished(field, { published_value: "https://carte" });
    updateMarker(field);
    assert.equal(badge(field).textContent, "+");
});
