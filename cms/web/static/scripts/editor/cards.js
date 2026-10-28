// MyCMS - cartes de l'éditeur : une carte par élément éditable de la page ouverte

import { $ } from "../core/dom.js";
import { setPublished, updateAllMarkers } from "./markers.js";
import { buildRichEditor, fieldValue, VOID_TAGS } from "./rich-editor.js";
import { state } from "../core/state.js";

export function renderElements(elements) {
    // Élément éditable le plus proche qui contient chaque élément imbriqué
    const parentOf = {};
    elements.forEach((elem) => elem.nested.forEach((n) => { parentOf[n] = elem.index; }));

    const fields = new Map();
    state.editor.fields = fields;
    const fragment = document.createDocumentFragment();
    for (const elem of elements) {
        const card = document.createElement("div");
        card.className = "field";
        card.id = `field-${elem.index}`;

        const meta = document.createElement("div");
        meta.className = "font-mono text-xs [overflow-wrap:anywhere]";
        const tag = document.createElement("div");
        tag.className = "font-bold text-tag";
        tag.textContent = `<${elem.tag.toUpperCase()}>${elem.is_iframe ? " [SRC]" : ""}`;
        const id = document.createElement("div");
        id.className = "text-muted";
        id.textContent = elem.id ? `#${elem.id} [${elem.index}]` : `[${elem.index}]`;
        // Différence avec la version envoyée sur GitHub : +, − ou ~ (voir updateMarker)
        const badge = document.createElement("span");
        badge.className = "pub-badge hidden";
        meta.append(tag, id, badge);
        if (elem.index in parentOf) {
            const inside = document.createElement("div");
            inside.className = "mt-1.5 text-muted";
            inside.textContent = `dans [${parentOf[elem.index]}]`;
            meta.append(inside);
        }

        let control;
        if (elem.is_iframe) {
            control = document.createElement("textarea");
            control.className = "input min-h-10 w-full resize-y";
            control.value = elem.value;
            control.rows = 1;
            fields.set(elem.index, { el: control, kind: "src", card });
        } else {
            const built = VOID_TAGS.has(elem.tag) ? null : buildRichEditor(elem);
            if (built) {
                control = built.editor;
                fields.set(elem.index, { el: control, kind: "rich", card, locks: built.locks });
            } else {
                control = document.createElement("p");
                control.className = "py-2 text-muted";
                control.textContent = VOID_TAGS.has(elem.tag)
                    ? "Élément sans contenu texte : non modifiable ici."
                    : "Structure HTML non reconnue : élément non modifiable ici.";
            }
        }

        card.append(meta, control);
        fragment.appendChild(card);
    }
    $("editable-list").replaceChildren(fragment);
    fields.forEach((field) => { field.initial = fieldValue(field); });
    elements.forEach((elem) => setPublished(fields.get(elem.index), elem));
    updateAllMarkers();
}
