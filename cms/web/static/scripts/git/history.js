// MyCMS - onglet Git : historique lisible (« Marie a modifié page/tarifs.html le 12 novembre à 14:03 »)

import { $, api, element, plural, toast } from "../core/dom.js";
import { buildDetails } from "./history-details.js";

const DATE = new Intl.DateTimeFormat("fr-FR", { dateStyle: "long", timeStyle: "short" });
const MAX_PAGES = 3;

// Phrase d'une modification : qui, quoi
export function describe(entry) {
    const pages = entry.pages.slice(0, MAX_PAGES).join(", ");
    const more = entry.pages.length - MAX_PAGES;
    const extra = [];
    if (more > 0) extra.push(plural(more, "autre page", "autres pages"));
    if (entry.other_files) extra.push(plural(entry.other_files, "autre fichier", "autres fichiers"));
    const what = pages || (entry.other_files ? plural(entry.other_files, "fichier", "fichiers") : "aucun fichier");
    const rest = pages && extra.length ? ` (et ${extra.join(", ")})` : "";
    return `${entry.author} a modifié ${what}${rest}`;
}

// Clic sur une modification : détail chargé une seule fois, puis déplié ou replié
async function toggleDetails(item, button, hash) {
    const open = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(open));
    let box = item.querySelector(".history-details");
    if (open && !box) {
        box = element("div", "history-details text-muted", "Chargement…");
        item.append(box);
        try {
            box.replaceChildren(buildDetails(await api("GET", `/api/git/commit/${encodeURIComponent(hash)}`)));
        } catch (e) {
            box.remove();
            button.setAttribute("aria-expanded", "false");
            toast(e.message, true);
            return;
        }
    }
    box?.classList.toggle("hidden", !open);
}

function historyItem(entry) {
    const item = element("li", "history-entry");
    const button = element("button", "history-summary");
    button.type = "button";
    button.setAttribute("aria-expanded", "false");
    button.title = "Voir ce qui a changé";
    const top = element("span", "flex flex-wrap items-center gap-2");
    top.append(element("span", "history-arrow", "▸"), element("span", "font-semibold [overflow-wrap:anywhere]", describe(entry)),
        element("span", entry.published ? "badge-on" : "badge-off", entry.published ? "Publié" : "Pas encore publié"));
    const details = `le ${DATE.format(new Date(entry.date))} · « ${entry.message} » · ${entry.hash}`;
    button.append(top, element("span", "text-xs text-muted [overflow-wrap:anywhere]", details));
    button.addEventListener("click", () => toggleDetails(item, button, entry.hash));
    item.append(button);
    return item;
}

export async function refreshHistory() {
    let entries = [];
    try {
        entries = (await api("GET", "/api/git/history")).entries;
    } catch {
        // Pas de repository, ou Git indisponible : l'onglet Git l'indique déjà dans le statut
    }
    $("git-history").replaceChildren(...(entries.length
        ? entries.map(historyItem)
        : [element("li", "text-muted", "Aucune modification enregistrée.")]));
}
