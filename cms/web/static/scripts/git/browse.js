// MyCMS - boutons « Parcourir… » : la fenêtre « Choisir un dossier » de Windows est ouverte par le serveur local,
// car le navigateur ne donne jamais le chemin complet d'un dossier

import { $, api, withButton } from "../core/dom.js";
import { useRepoPath } from "./git.js";
import { state } from "../core/state.js";

export function initBrowse() {
    document.querySelectorAll("[data-browse]").forEach((button) => {
        button.addEventListener("click", () => withButton(button, async () => {
            const input = $(button.dataset.browse);
            const result = await api("POST", "/api/browse-folder", {
                title: button.dataset.browseTitle,
                start: input.value.trim() || state.config.repo_path || "",
            });
            if (result.cancelled || !result.path) return;
            input.value = result.path;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            // Onglet Git : le dossier choisi est utilisé tout de suite, comme avec « Vérifier »
            if (button.dataset.browse === "git-repo") await useRepoPath();
        }));
    });
}
