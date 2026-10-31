// MyCMS - aperçu, onglet Code : lignes du code source de l'élément, telles qu'elles seraient sauvegardées

import { $, api } from "../core/dom.js";
import { dirtyValues, fileUrl } from "../editor/editor.js";
import { state } from "../core/state.js";

const snippet = { request: 0, shown: null }; // Dernière demande envoyée, élément affiché

export function setPaneInfo(text) {
    $("pane-info").textContent = text;
    $("pane-info").title = text;
}

export function paneMessage(text) {
    const p = document.createElement("p");
    p.className = "px-3 py-10 text-center font-sans text-sm text-muted";
    p.textContent = text;
    return p;
}

export async function refreshSnippet(index) {
    const view = $("code-view");
    if (index === null) {
        snippet.shown = null;
        view.replaceChildren(paneMessage("Cliquez dans un élément pour afficher son code source."));
        setPaneInfo("");
        return;
    }
    const request = ++snippet.request;
    let data;
    try {
        data = await api("POST", fileUrl(state.editor.file, "/api/snippet/"), { hash: state.editor.hash, values: dirtyValues(), index });
    } catch (e) {
        if (request === snippet.request) view.replaceChildren(paneMessage(e.message));
        return;
    }
    if (request !== snippet.request) return; // Une réponse plus récente arrive

    const fragment = document.createDocumentFragment();
    data.lines.forEach((text, k) => {
        const number = data.first_line + k;
        const line = document.createElement("div");
        line.className = number >= data.start_line && number <= data.end_line ? "code-line hl" : "code-line";
        const ln = document.createElement("span");
        ln.className = "ln";
        ln.textContent = number;
        const code = document.createElement("span");
        code.className = "pr-3";
        code.textContent = text || " ";
        line.append(ln, code);
        fragment.append(line);
    });
    view.replaceChildren(fragment);
    if (snippet.shown !== index) view.scrollTop = 0;
    snippet.shown = index;

    const dirty = $(`field-${index}`)?.classList.contains("dirty");
    const lines = data.start_line === data.end_line ? `ligne ${data.start_line}` : `lignes ${data.start_line} à ${data.end_line}`;
    setPaneInfo(`[${index}] · ${lines}${dirty ? " · non sauvegardé" : ""}`);
}
