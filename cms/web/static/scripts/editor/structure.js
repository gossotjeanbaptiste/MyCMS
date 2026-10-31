// MyCMS - actions des cartes : revenir à la version en ligne, dupliquer ou supprimer un élément de liste
// ou une ligne de tableau (le fichier est alors modifié tout de suite, puis la page est rechargée)

import { $, api, toast } from "../core/dom.js";
import { dirtyCount, fileUrl, markDirty, openFile, saveCurrentFile } from "./editor.js";
import { restorePublished } from "./markers.js";
import { state } from "../core/state.js";

const editor = state.editor;

function restore(index) {
    const field = editor.fields.get(index);
    if (!restorePublished(field)) {
        toast("Impossible de remettre la version en ligne automatiquement : les éléments imbriqués ont changé.", true);
        return;
    }
    markDirty(index);
    toast("Version en ligne remise : sauvegardez pour l'enregistrer.");
}

// Dupliquer ou supprimer change la place des éléments : on enregistre d'abord ce qui ne l'est pas
async function changeStructure(action, index, button) {
    const card = $(`field-${index}`);
    const what = card.querySelector(".card-actions").dataset.what;
    if (action === "delete" && !confirm(`Supprimer ${what} ? La page est modifiée tout de suite (pas encore publiée).`)) return;
    if (dirtyCount()) {
        if (!confirm("Les modifications non sauvegardées vont d'abord être sauvegardées. Continuer ?")) return;
        await saveCurrentFile();
    }
    button.disabled = true;
    try {
        const result = await api("POST", fileUrl(editor.file, "/api/structure/"), { hash: editor.hash, action, index });
        await openFile(editor.file, { keepScroll: true });
        toast(result.message);
        // Copie : aller à sa carte, prête à être modifiée
        const copy = result.focus != null && $(`field-${result.focus}`);
        if (copy) {
            copy.scrollIntoView({ behavior: "smooth", block: "center" });
            editor.fields.get(result.focus)?.el.focus({ preventScroll: true });
        }
    } finally {
        button.disabled = false;
    }
}

export function initStructure() {
    $("editable-list").addEventListener("click", (e) => {
        const button = e.target.closest(".card-actions [data-action]");
        if (!button) return;
        const index = Number(button.closest(".field").id.slice("field-".length));
        if (button.dataset.action === "restore") restore(index);
        else changeStructure(button.dataset.action, index, button).catch((err) => toast(err.message, true));
    });
}
