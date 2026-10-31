// MyCMS - nouvelle version publiée sur GitHub : lien dans l'en-tête

import { $, api } from "../core/dom.js";

// Appelée au démarrage par main.js ; sans réseau, rien n'est affiché
export async function checkForUpdate() {
    let update;
    try {
        update = await api("GET", "/api/update");
    } catch {
        return;
    }
    const link = $("update-link");
    link.classList.toggle("hidden", !update.available);
    if (!update.available) return;
    link.href = update.url;
    link.textContent = `Nouvelle version ${update.latest}`;
    link.title = `Vous avez MyCMS ${update.current}. Télécharger et installer la version ${update.latest}`;
}
