// MyCMS - onglet Prévisualisation : serveur local qui sert les fichiers du site

import { $, api, toast, withButton } from "../core/dom.js";
import { state } from "../core/state.js";
import { onTabOpen } from "../core/tabs.js";

const polling = { timer: null }; // Rafraîchissement de l'état tant que l'onglet est ouvert

export function showPreview(status) {
    state.preview.running = status.running;
    $("preview-state").className = status.running ? "badge-on" : "badge-off";
    $("preview-state").textContent = status.running ? `Actif (port ${status.port})` : "Arrêté";
    $("preview-toggle").textContent = status.running ? "Arrêter" : "Démarrer";
    $("preview-port").disabled = status.running;
    const url = status.running ? `http://127.0.0.1:${status.port}` : "";
    $("preview-url").href = url || "#";
    $("preview-url").textContent = url;
    $("preview-logs").textContent = status.logs.join("\n");
}

export async function refreshPreview() {
    showPreview(await api("GET", "/api/preview"));
}

export function stopPreviewPolling() {
    clearInterval(polling.timer);
}

export function initPreview() {
    onTabOpen("preview", () => {
        refreshPreview();
        clearInterval(polling.timer);
        polling.timer = setInterval(() => {
            if ($("tab-preview").classList.contains("active")) refreshPreview();
            else clearInterval(polling.timer);
        }, 2000);
    });

    $("preview-toggle").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (state.preview.running) {
            showPreview(await api("POST", "/api/preview/stop"));
            toast("Serveur arrêté");
        } else {
            const status = await api("POST", "/api/preview/start", { port: Number($("preview-port").value) });
            showPreview(status);
            toast(`Serveur local démarré sur http://127.0.0.1:${status.port}`);
        }
    }));
}
