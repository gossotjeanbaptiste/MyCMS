// MyCMS - onglet Prévisualisation : serveur local qui sert les fichiers du site

import { $, api, toast, withButton } from "../core/dom.js";
import { createPoller } from "../core/poller.js";
import { state } from "../core/state.js";
import { onTabOpen } from "../core/tabs.js";

// Lignes du journal déjà affichées : on ne redemande que les suivantes
const journal = { seen: 0 };

export function showPreview(status) {
    state.preview.running = status.running;
    $("preview-state").className = status.running ? "badge-on" : "badge-off";
    $("preview-state").textContent = status.running ? `Actif (port ${status.port})` : "Arrêté";
    $("preview-toggle").textContent = status.running ? "Arrêter" : "Démarrer";
    $("preview-port").disabled = status.running;
    const url = status.running ? `http://127.0.0.1:${status.port}` : "";
    $("preview-url").href = url || "#";
    $("preview-url").textContent = url;
    const output = $("preview-logs");
    if (status.reset) output.textContent = status.logs.join("\n");
    else if (status.logs.length) output.textContent += (output.textContent ? "\n" : "") + status.logs.join("\n");
    journal.seen = status.total;
}

// Toutes les 2 secondes, seulement si l'onglet est ouvert et le serveur lancé (sinon rien ne peut changer)
const poller = createPoller(2000,
    async () => showPreview(await api("GET", `/api/preview?since=${journal.seen}`)),
    () => state.preview.running && $("tab-preview").classList.contains("active"));

export async function refreshPreview() {
    showPreview(await api("GET", "/api/preview"));
}

export function stopPreviewPolling() {
    poller.stop();
}

export function initPreview() {
    onTabOpen("preview", () => refreshPreview().then(poller.start).catch((e) => toast(e.message, true)));

    $("preview-toggle").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (state.preview.running) {
            showPreview(await api("POST", "/api/preview/stop"));
            toast("Serveur arrêté");
        } else {
            const status = await api("POST", "/api/preview/start", { port: Number($("preview-port").value) });
            showPreview(status);
            poller.start();
            toast(`Serveur local démarré sur http://127.0.0.1:${status.port}`);
        }
    }));
}
