// MyCMS - catégories de l'éditeur : filtre de la liste par partie de la page (déduite par le serveur)

import { $, element } from "../core/dom.js";
import { applySearch, clearSearch } from "./search.js";
import { state } from "../core/state.js";

const editor = state.editor;

function chip(label, category, count) {
    const button = element("button", "chip");
    button.type = "button";
    button.dataset.category = category;
    button.setAttribute("aria-pressed", String(category === editor.category));
    button.title = category ? `Afficher seulement « ${category} »` : "Afficher tous les éléments";
    // Nom complet dans l'infobulle : raccourci à l'affichage s'il est trop long
    button.append(element("span", "max-w-72 truncate", label), element("span", "count", String(count)), element("span", "dot"));
    return button;
}

// Barre des catégories de la page ouverte, dans l'ordre de la page (masquée s'il n'y en a qu'une)
export function renderCategories(elements) {
    const counts = new Map();
    elements.forEach((elem) => counts.set(elem.category, (counts.get(elem.category) || 0) + 1));
    // Catégorie choisie avant un rechargement : gardée si elle existe encore
    if (!counts.has(editor.category)) editor.category = "";
    const bar = $("category-bar");
    if (counts.size < 2) {
        editor.category = "";
        bar.replaceChildren();
        bar.classList.add("hidden");
        return;
    }
    bar.replaceChildren(chip("Tout", "", elements.length),
        ...[...counts].map(([category, count]) => chip(category, category, count)));
    bar.classList.remove("hidden");
    updateCategoryDirty();
}

export function selectCategory(category) {
    editor.category = category;
    $("category-bar").querySelectorAll(".chip").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.category === category));
    });
    applySearch();
    $("editable-list").scrollTop = 0;
}

// Point sur les catégories qui ont des modifications non sauvegardées
export function updateCategoryDirty() {
    const dirty = new Set([...document.querySelectorAll("#editable-list .field.dirty")].map((c) => c.dataset.category));
    $("category-bar").querySelectorAll(".chip").forEach((button) => {
        const category = button.dataset.category;
        button.classList.toggle("dirty", category ? dirty.has(category) : dirty.size > 0);
    });
}

// Carte masquée par le filtre ou la recherche (clic dans l'aperçu, bloc verrouillé) : tout réafficher
export function revealCard(card) {
    if (!card?.classList.contains("hidden")) return;
    if (editor.category) selectCategory("");
    if (card.classList.contains("hidden")) clearSearch();
}

export function initCategories() {
    $("category-bar").addEventListener("click", (e) => {
        const button = e.target.closest(".chip");
        if (button) selectCategory(button.dataset.category);
    });
}
