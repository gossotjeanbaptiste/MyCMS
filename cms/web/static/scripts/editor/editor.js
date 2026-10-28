// MyCMS - éditeur : liste des pages, ouverture, saisie, sauvegarde

import { $, api, toast, withButton } from "../core/dom.js";
import { renderElements } from "./cards.js";
import { updateMarker } from "./markers.js";
import { forgetPaneElement, refreshPane, schedulePaneUpdate } from "../preview/pane.js";
import { applySiteBoldRules, fieldValue } from "./rich-editor.js";
import { applySearch } from "./search.js";
import { state } from "../core/state.js";

const editor = state.editor;

export async function loadFiles() {
    const { files } = await api("GET", "/api/files");
    const select = $("file-select");
    select.replaceChildren(new Option("Choisir un fichier…", ""));
    files.forEach((f) => select.add(new Option(f, f)));
    if (files.includes(editor.file)) select.value = editor.file;
    return files;
}

// Les pages peuvent être dans des sous-dossiers : encoder chaque segment, garder les "/"
export function fileUrl(name, prefix = "/api/files/") {
    return prefix + name.split("/").map(encodeURIComponent).join("/");
}

export function dirtyCount() {
    return document.querySelectorAll("#editable-list .field.dirty").length;
}

export function updateEditorState() {
    const dirty = dirtyCount();
    $("save-file").disabled = !editor.file || dirty === 0;
    $("save-file").textContent = dirty ? `Sauvegarder (${dirty})` : "Sauvegarder";
    $("reload-file").disabled = !editor.file;
}

// Après un push ou un pull, la version publiée change : recharger la page ouverte (si rien n'est en cours d'édition)
export async function refreshPublished() {
    if (editor.file && !dirtyCount()) await openFile(editor.file, { keepScroll: true });
}

export async function openFile(name, { keepScroll = false } = {}) {
    if (!name) return;
    if (dirtyCount() && !confirm("Des modifications non sauvegardées seront perdues. Continuer ?")) {
        $("file-select").value = editor.file || "";
        return;
    }
    const scroll = keepScroll ? $("editable-list").scrollTop : 0;
    const start = performance.now();
    const data = await api("GET", fileUrl(name));
    // Page mise à jour mais serveur Python lancé avant : il ne renvoie pas encore ces champs
    if (data.elements.some((e) => !("html" in e) || !Array.isArray(e.nested))) {
        throw new Error("Le serveur MyCMS tourne sur une ancienne version : fermez la fenêtre de run.bat et relancez-le.");
    }

    if (name !== editor.file) forgetPaneElement();
    editor.file = name;
    editor.hash = data.hash;
    editor.publishedKnown = Boolean(data.published_known);
    editor.elementCount = data.elements.length;
    applySiteBoldRules(data.bold_selectors || []);

    if (data.elements.length) {
        renderElements(data.elements);
    } else {
        editor.fields = new Map();
        const p = document.createElement("p");
        p.className = "py-10 text-center text-muted";
        p.textContent = data.notice || "Aucun élément éditable trouvé";
        $("editable-list").replaceChildren(p);
    }
    applySearch();
    $("editable-list").scrollTop = scroll;

    const total = Math.round(performance.now() - start);
    $("editor-info").textContent = `${data.elements.length} éléments · ${total} ms`;
    updateEditorState();
    refreshPane();
}

export function markDirty(index) {
    const field = editor.fields.get(index);
    if (field) field.card.classList.toggle("dirty", fieldValue(field) !== field.initial);
    updateMarker(field);
    updateEditorState();
    schedulePaneUpdate();
}

// Valeurs des éléments modifiés, par index
export function dirtyValues() {
    const values = {};
    editor.fields.forEach((field, index) => {
        if (field.card.classList.contains("dirty")) values[index] = fieldValue(field);
    });
    return values;
}

// Seuls les éléments modifiés sont envoyés
export async function saveCurrentFile() {
    const result = await api("POST", fileUrl(editor.file), { hash: editor.hash, values: dirtyValues() });
    document.querySelectorAll("#editable-list .field.dirty").forEach((f) => f.classList.remove("dirty"));
    // Empreinte du fichier tel qu'écrit : une nouvelle sauvegarde sans rechargement reste acceptée
    editor.hash = result.hash;
    return result;
}

export function warnUnsaved(e) {
    if (dirtyCount()) e.preventDefault();
}

export function initEditor() {
    $("file-select").addEventListener("change", (e) => {
        openFile(e.target.value).catch((err) => toast(err.message, true));
    });

    $("refresh-files").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const files = await loadFiles();
        toast(`${files.length} fichiers trouvés`);
    }));

    $("reload-file").addEventListener("click", (e) => withButton(e.currentTarget, () => openFile(editor.file, { keepScroll: true })));

    $("save-file").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const result = await saveCurrentFile();
        toast(`${result.message}\n${result.sitemap}`);
        // Recharger depuis le fichier : l'éditeur affiche exactement ce qui a été écrit
        await openFile(editor.file, { keepScroll: true });
    }).then(updateEditorState));

    window.addEventListener("beforeunload", warnUnsaved);
}
