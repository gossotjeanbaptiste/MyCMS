// MyCMS - onglet Git : historique lisible (« Marie a modifié page/tarifs.html le 12 novembre à 14:03 »)

import { $, api, element, plural } from "../core/dom.js";

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

function historyItem(entry) {
    const item = element("li", "flex flex-col gap-0.5 rounded-lg border border-line px-3 py-2");
    const top = element("div", "flex flex-wrap items-center gap-2");
    top.append(element("span", "font-semibold [overflow-wrap:anywhere]", describe(entry)),
        element("span", entry.published ? "badge-on" : "badge-off", entry.published ? "Publié" : "Pas encore publié"));
    const details = `le ${DATE.format(new Date(entry.date))} · « ${entry.message} » · ${entry.hash}`;
    item.append(top, element("span", "text-xs text-muted [overflow-wrap:anywhere]", details));
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
