// MyCMS - éditeur : brouillon des modifications non sauvegardées, gardé dans le navigateur (localStorage).
// Onglet fermé par erreur, PC redémarré : à la réouverture de la page, l'éditeur propose de les remettre.

import { toast } from "../core/dom.js";
import { state } from "../core/state.js";

const editor = state.editor;
const draft = { timer: 0 };
const DELAY = 500; // Une écriture par pause dans la saisie, pas une par touche

const key = (file) => `mycms-draft:${file}`;

function read(file) {
    try {
        return JSON.parse(localStorage.getItem(key(file)) || "null");
    } catch {
        return null; // Stockage bloqué (navigation privée…) : pas de brouillon
    }
}

export function clearDraft(file = editor.file) {
    if (!file) return;
    clearTimeout(draft.timer);
    try {
        localStorage.removeItem(key(file));
    } catch {
        // Stockage indisponible : rien à effacer
    }
}

// Contenu brut des champs modifiés : le HTML de l'éditeur enrichi (verrous compris), ou la valeur d'un champ
function writeDraft() {
    clearTimeout(draft.timer);
    if (!editor.file) return;
    const values = {};
    editor.fields.forEach((field, index) => {
        if (field.card.classList.contains("dirty")) values[index] = field.kind === "rich" ? field.el.innerHTML : field.el.value;
    });
    if (!Object.keys(values).length) return clearDraft();
    try {
        localStorage.setItem(key(editor.file), JSON.stringify({ hash: editor.hash, saved: Date.now(), values }));
    } catch {
        // Stockage plein ou bloqué : le brouillon n'est simplement pas gardé
    }
}

// Appelée à chaque modification d'un champ (markDirty)
export function scheduleDraft() {
    clearTimeout(draft.timer);
    draft.timer = setTimeout(writeDraft, DELAY);
}

// Après l'ouverture d'une page : proposer le brouillon retrouvé, s'il correspond au fichier tel qu'il est
export function offerDraft() {
    const found = read(editor.file);
    if (!found?.values) return;
    if (found.hash !== editor.hash) {
        // Les éléments ont pu changer de place : remettre le brouillon pourrait modifier les mauvais textes
        clearDraft();
        toast("Des modifications non sauvegardées de cette page avaient été gardées, mais la page a changé depuis : "
            + "elles ne peuvent pas être remises.", true);
        return;
    }
    const when = new Date(found.saved).toLocaleString("fr-FR", { dateStyle: "long", timeStyle: "short" });
    const count = Object.keys(found.values).length;
    if (!confirm(`Des modifications non sauvegardées de cette page ont été retrouvées (${count} élément(s), le ${when}).`
        + "\n\nLes remettre dans l'éditeur ? Il faudra ensuite les sauvegarder.")) {
        clearDraft();
        return;
    }
    Object.entries(found.values).forEach(([index, value]) => {
        const field = editor.fields.get(Number(index));
        if (!field) return;
        if (field.kind === "rich") field.el.innerHTML = value;
        else field.el.value = value;
        // Même chemin qu'une saisie : carte marquée modifiée, marqueurs, aperçu, vignette d'une image
        field.el.dispatchEvent(new Event("input", { bubbles: true }));
    });
}

export function initDraft() {
    // Onglet fermé juste après une saisie : écrire sans attendre la fin du délai
    window.addEventListener("pagehide", writeDraft);
}
