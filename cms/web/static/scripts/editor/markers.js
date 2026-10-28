// MyCMS - marqueurs « pas encore publié »
// Chaque élément est comparé à sa version envoyée sur GitHub : + plus de contenu, − moins, ~ autant.
// Ils restent affichés jusqu'au push (modifications non sauvegardées comprises).

import { $ } from "../core/dom.js";
import { buildRichEditor, fieldValue, serializeRich } from "./rich-editor.js";
import { state } from "../core/state.js";

const MARKERS = {
    add: { symbol: "+", title: "Plus de contenu que la version publiée sur GitHub" },
    del: { symbol: "−", title: "Moins de contenu que la version publiée sur GitHub" },
    mod: { symbol: "~", title: "Contenu modifié, de même longueur que la version publiée sur GitHub" },
};

function textLength(text) {
    return text.replace(/\s+/g, " ").trim().length;
}

// Version publiée mise dans la même forme que fieldValue() : même passage par l'éditeur
export function setPublished(field, elem) {
    if (!field) return;
    field.published = undefined;
    if (!state.editor.publishedKnown) return;
    if (field.kind === "src") {
        field.published = elem.published_value == null ? null : { value: elem.published_value, length: elem.published_value.length };
        return;
    }
    if (elem.published_html == null) {
        field.published = null; // Élément absent de la version publiée
        return;
    }
    const built = buildRichEditor({ ...elem, html: elem.published_html });
    field.published = built
        ? { value: serializeRich(built.editor), length: textLength(built.editor.textContent) }
        : { value: null, length: textLength(elem.published_value || "") };
}

function publishMarker(field) {
    if (!state.editor.publishedKnown || field.published === undefined) return "";
    const current = fieldValue(field);
    if (field.published === null) return textLength(field.kind === "rich" ? field.el.textContent : current) ? "add" : "";
    if (current === field.published.value) return "";
    const length = textLength(field.kind === "rich" ? field.el.textContent : current);
    if (field.published.value === null && length === field.published.length) return ""; // Comparaison du texte seul
    return length > field.published.length ? "add" : length < field.published.length ? "del" : "mod";
}

export function updateMarker(field) {
    if (!field) return;
    const marker = publishMarker(field);
    field.card.classList.remove("pub-add", "pub-del", "pub-mod");
    const badge = field.card.querySelector(".pub-badge");
    if (marker) {
        field.card.classList.add(`pub-${marker}`);
        badge.textContent = MARKERS[marker].symbol;
        badge.title = MARKERS[marker].title;
    }
    badge.classList.toggle("hidden", !marker);
    $("pub-legend").classList.toggle("hidden", !document.querySelector("#editable-list .pub-badge:not(.hidden)"));
}

export function updateAllMarkers() {
    state.editor.fields.forEach(updateMarker);
    $("pub-legend").classList.toggle("hidden", !document.querySelector("#editable-list .pub-badge:not(.hidden)"));
}
