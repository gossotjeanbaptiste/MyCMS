// MyCMS - cartes de l'éditeur : une carte par élément éditable de la page ouverte

import { $, element } from "../core/dom.js";
import { buildImageField } from "./image-field.js";
import { setPublished, updateAllMarkers } from "./markers.js";
import { buildRichEditor, fieldValue, VOID_TAGS } from "./rich-editor.js";
import { state } from "../core/state.js";

// Actions de la carte (voir structure.js) : revenir à la version en ligne (affichée avec un marqueur),
// dupliquer ou supprimer l'élément de liste ou la ligne de tableau
function cardActions(elem) {
    // Petits boutons sur une ligne : le libellé complet est dans l'infobulle (et lu par les lecteurs d'écran)
    const actions = element("div", "card-actions mt-2 flex flex-wrap gap-1 font-sans");
    const button = (action, icon, title, hidden = false) => {
        const b = element("button", `fmt min-h-7 min-w-7 text-sm${hidden ? " hidden" : ""}`, icon);
        b.type = "button";
        b.dataset.action = action;
        b.title = title;
        b.setAttribute("aria-label", title);
        actions.append(b);
    };
    button("restore", "↺", "Version en ligne : remettre le contenu publié sur GitHub (à sauvegarder ensuite)", true);
    if (elem.repeat) {
        const what = elem.repeat === "tr" ? "la ligne du tableau" : "l'élément de la liste";
        actions.dataset.what = what;
        button("duplicate", "＋", `Dupliquer : ajouter une copie de ${what} juste après`);
        button("delete", "✕", `Supprimer ${what}`);
    }
    return actions;
}

export function renderElements(elements) {
    // Élément éditable le plus proche qui contient chaque élément imbriqué
    const parentOf = {};
    elements.forEach((elem) => elem.nested.forEach((n) => { parentOf[n] = elem.index; }));

    const fields = new Map();
    state.editor.fields = fields;
    const fragment = document.createDocumentFragment();
    let category = null;
    for (const elem of elements) {
        // Intertitre à chaque changement de catégorie (voir categories.js)
        if (elem.category !== category) {
            category = elem.category;
            const title = document.createElement("h3");
            title.className = "category-title";
            title.textContent = category;
            fragment.appendChild(title);
        }
        const card = document.createElement("div");
        card.className = "field";
        card.id = `field-${elem.index}`;
        card.dataset.category = elem.category;

        const meta = document.createElement("div");
        meta.className = "font-mono text-xs [overflow-wrap:anywhere]";
        const tag = document.createElement("div");
        tag.className = "font-bold text-tag";
        tag.textContent = `<${elem.tag.toUpperCase()}>${elem.is_iframe || elem.is_image ? " [SRC]" : ""}`;
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
        meta.append(cardActions(elem));

        let control;
        if (elem.is_image) {
            const image = buildImageField(elem);
            control = image.control;
            fields.set(elem.index, { el: image.input, kind: "src", card });
        } else if (elem.is_iframe) {
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
