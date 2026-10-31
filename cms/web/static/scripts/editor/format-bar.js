// MyCMS - barre de mise en forme : gras, italique, liens, appliqués à l'élément en cours d'édition

import { $, toast } from "../core/dom.js";
import { markDirty } from "./editor.js";

function selectionElement() {
    const node = document.getSelection()?.anchorNode;
    return node && (node.nodeType === 1 ? node : node.parentElement);
}

function activeEditor() {
    return selectionElement()?.closest("#editable-list .rich") || null;
}

function updateFormatBar() {
    const editor = activeEditor();
    document.querySelectorAll("#format-bar .fmt").forEach((button) => {
        button.disabled = !editor;
        const cmd = button.dataset.cmd;
        if (cmd === "bold" || cmd === "italic") {
            button.setAttribute("aria-pressed", editor && document.queryCommandState(cmd) ? "true" : "false");
        }
    });
    $("format-hint").textContent = editor
        ? `Élément [${editor.dataset.index}] : sélectionnez du texte puis appliquez une mise en forme`
        : "Cliquez dans un élément pour le modifier.";
}

function applyFormat(button) {
    const editor = activeEditor();
    if (!editor) return;
    const cmd = button.dataset.cmd;
    if (cmd === "bold" && document.queryCommandState("bold") && !selectionElement()?.closest(".rich strong, .rich b")) {
        // Le navigateur ajouterait un <span style="font-weight: normal">, retiré à la sauvegarde
        const reason = ["strong", "b"].includes(editor.dataset.tag)
            ? `cet élément est déjà lui-même une balise <${editor.dataset.tag}>`
            : "le CSS du site met déjà ce texte en gras";
        toast(`Le CMS n'autorise pas à retirer le gras ici : ${reason}.`, true);
        return;
    }
    if (cmd === "link") {
        const current = selectionElement()?.closest("a");
        const url = prompt("Adresse du lien (https://…, page.html, mailto:…)", current?.getAttribute("href") || "https://");
        if (url && url.trim() && url.trim() !== "https://") document.execCommand("createLink", false, url.trim());
    } else if (cmd === "removeFormat") {
        document.execCommand("removeFormat");
        document.execCommand("unlink");
    } else {
        document.execCommand(cmd);
    }
    markDirty(Number(editor.dataset.index));
    updateFormatBar();
}

export function initFormatBar() {
    document.addEventListener("selectionchange", updateFormatBar);
    document.querySelectorAll("#format-bar .fmt").forEach((button) => {
        // mousedown : garder la sélection dans l'éditeur
        button.addEventListener("mousedown", (e) => e.preventDefault());
        button.addEventListener("click", () => applyFormat(button));
    });
    updateFormatBar();
}
