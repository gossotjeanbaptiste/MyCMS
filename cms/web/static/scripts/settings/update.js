// MyCMS - nouvelle version publiée sur GitHub : bouton dans l'en-tête, qui installe la mise à jour
// (administrateur, application installée) ou mène à la page de la release

import { $, api, toast } from "../core/dom.js";
import { state } from "../core/state.js";
import { dirtyCount, saveCurrentFile } from "../editor/editor.js";
import { showClosedScreen } from "../quit/quit.js";

const update = { info: null, busy: false };

// Le serveur télécharge le .msi, lance l'installeur et se ferme ; l'installeur relance MyCMS à la fin
async function install(e) {
    if (!update.info?.auto || !state.user.admin) return; // Lien vers la release
    e.preventDefault();
    if (update.busy) return;
    const version = update.info.latest;
    const unsaved = dirtyCount() ? "\n\nLes modifications non sauvegardées seront d'abord sauvegardées." : "";
    if (!confirm(`Installer MyCMS ${version} ? MyCMS va se fermer, s'installer puis se relancer tout seul.` +
        "\nWindows peut demander l'autorisation d'administrateur." + unsaved)) return;
    const link = $("update-link");
    update.busy = true;
    link.textContent = "Téléchargement…";
    try {
        if (dirtyCount()) await saveCurrentFile();
        await api("POST", "/api/update/install");
    } catch (err) {
        update.busy = false;
        link.textContent = `Nouvelle version ${version}`;
        toast(err.message, true);
        return;
    }
    showClosedScreen(`Installation de MyCMS ${version} en cours : il se relancera tout seul à la fin, dans un nouvel onglet.`);
}

// Appelée au démarrage par main.js ; sans réseau, rien n'est affiché
export async function checkForUpdate() {
    try {
        update.info = await api("GET", "/api/update");
    } catch {
        return;
    }
    const info = update.info;
    const link = $("update-link");
    link.classList.toggle("hidden", !info.available);
    if (!info.available) return;
    const auto = info.auto && state.user.admin;
    link.href = info.url;
    link.textContent = `Nouvelle version ${info.latest}`;
    link.title = auto ? `Vous avez MyCMS ${info.current}. Installer la version ${info.latest} maintenant`
        : `Vous avez MyCMS ${info.current}. Télécharger et installer la version ${info.latest}`;
    link.addEventListener("click", install);
}
