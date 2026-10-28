// MyCMS - onglet Logs : journal de l'application, rafraîchi tant que l'onglet est ouvert

import { $, api, toast, withButton } from "../core/dom.js";
import { onTabOpen } from "../core/tabs.js";

const polling = { timer: null };

async function refreshLogs() {
    const output = $("logs-output");
    const wasAtBottom = output.scrollTop + output.clientHeight >= output.scrollHeight - 20;
    output.textContent = (await api("GET", "/api/logs")).logs.join("\n");
    if (wasAtBottom) output.scrollTop = output.scrollHeight;
}

export function stopLogsPolling() {
    clearInterval(polling.timer);
}

export function initLogs() {
    onTabOpen("logs", () => {
        refreshLogs();
        clearInterval(polling.timer);
        polling.timer = setInterval(() => {
            if ($("tab-logs").classList.contains("active")) refreshLogs();
            else clearInterval(polling.timer);
        }, 1000);
    });

    $("logs-clear").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        await api("DELETE", "/api/logs");
        await refreshLogs();
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
