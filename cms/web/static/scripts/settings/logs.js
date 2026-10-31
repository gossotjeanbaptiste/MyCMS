// MyCMS - onglet Logs : journal de l'application, rafraîchi tant que l'onglet est ouvert

import { $, api, toast, withButton } from "../core/dom.js";
import { createPoller } from "../core/poller.js";
import { onTabOpen } from "../core/tabs.js";

// Lignes déjà affichées : on ne redemande que les suivantes
const journal = { seen: 0 };

// full : tout le journal (ouverture de l'onglet, après « Effacer ») ; sinon seulement les nouvelles lignes
async function refreshLogs(full = false) {
    const output = $("logs-output");
    const wasAtBottom = output.scrollTop + output.clientHeight >= output.scrollHeight - 20;
    const data = await api("GET", full ? "/api/logs" : `/api/logs?since=${journal.seen}`);
    if (data.reset) output.textContent = data.logs.join("\n");
    else if (data.logs.length) output.textContent += (output.textContent ? "\n" : "") + data.logs.join("\n");
    journal.seen = data.total;
    if (wasAtBottom) output.scrollTop = output.scrollHeight;
}

// Toutes les secondes, seulement si l'onglet est ouvert (et la fenêtre visible)
const poller = createPoller(1000, () => refreshLogs(), () => $("tab-logs").classList.contains("active"));

export function stopLogsPolling() {
    poller.stop();
}

export function initLogs() {
    onTabOpen("logs", () => refreshLogs(true).then(poller.start).catch((e) => toast(e.message, true)));

    $("logs-clear").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        await api("DELETE", "/api/logs");
        await refreshLogs(true);
        toast("Logs effacés");
    }));

    $("logs-export").addEventListener("click", () => {
        const blob = new Blob([$("logs-output").textContent], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `mycms-logs-${new Date().toISOString().slice(0, 10)}.txt`;
        link.click();
        URL.revokeObjectURL(link.href);
    });
}
