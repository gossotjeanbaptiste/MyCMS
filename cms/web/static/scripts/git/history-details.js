// MyCMS - détail d'une modification de l'historique : textes changés page par page, puis le code modifié

import { element, plural } from "../core/dom.js";

const KINDS = {
    modified: { label: "Modifié", badge: "pub-badge-mod" },
    formatted: { label: "Mise en forme", badge: "pub-badge-mod" },
    added: { label: "Ajouté", badge: "pub-badge-add" },
    removed: { label: "Supprimé", badge: "pub-badge-del" },
};
const PAGE_STATUS = { added: " (nouvelle page)", removed: " (page supprimée)", modified: "" };

// Texte avec les mots supprimés barrés et les mots ajoutés surlignés
function wordsLine(words) {
    const line = element("p", "[overflow-wrap:anywhere]");
    words.forEach((w) => line.append(w.op === "equal" ? document.createTextNode(w.text)
        : element("span", w.op === "del" ? "diff-del" : "diff-ins", w.text)));
    return line;
}

function changeItem(change) {
    const item = element("li", "flex flex-col gap-1 rounded-md border border-line px-3 py-2");
    const top = element("div", "flex flex-wrap items-center gap-2 text-xs");
    top.append(element("span", `pub-badge ${KINDS[change.kind].badge} mt-0 px-2 font-sans`, KINDS[change.kind].label),
        element("span", "text-muted", change.category));
    item.append(top);
    if (change.kind === "modified") item.append(wordsLine(change.words));
    else if (change.kind === "added") item.append(wordsLine([{ op: "ins", text: change.after || "(vide)" }]));
    else if (change.kind === "removed") item.append(wordsLine([{ op: "del", text: change.before || "(vide)" }]));
    else item.append(element("p", "[overflow-wrap:anywhere]", change.after), element("p", "text-xs text-muted",
        "Même texte : le gras, l'italique ou un lien a changé."));
    return item;
}

// Code modifié (diff Git), replié : pour un développeur
function codeDetails(diff) {
    const details = element("details", "text-xs");
    details.append(element("summary", "cursor-pointer text-muted", "Voir le code modifié"));
    const pre = element("pre", "mt-1 max-h-80 overflow-auto rounded-md bg-surface-2 p-2 font-mono");
    diff.split("\n").forEach((line) => {
        const cls = line.startsWith("+") && !line.startsWith("+++") ? "diff-ins"
            : line.startsWith("-") && !line.startsWith("---") ? "diff-del" : "";
        pre.append(element("span", `block ${cls}`, line || " "));
    });
    details.append(pre);
    return details;
}

function pageSection(page) {
    const section = element("section", "flex flex-col gap-1.5");
    section.append(element("h4", "font-semibold [overflow-wrap:anywhere]", `${page.path}${PAGE_STATUS[page.status]}`));
    if (!page.changes.length) {
        section.append(element("p", "text-muted", "Aucun texte modifiable n'a changé : la modification porte sur le code de la page."));
    } else {
        const list = element("ul", "flex flex-col gap-1.5");
        page.changes.forEach((change) => list.append(changeItem(change)));
        section.append(list);
        if (page.total > page.changes.length) {
            section.append(element("p", "text-xs text-muted", `… et ${plural(page.total - page.changes.length, "autre changement", "autres changements")}`));
        }
    }
    if (page.diff) section.append(codeDetails(page.diff));
    return section;
}

// Contenu déplié sous une modification de l'historique
export function buildDetails(details) {
    const box = element("div", "flex flex-col gap-3 border-t border-line pt-2");
    if (details.message.includes("\n")) box.append(element("p", "whitespace-pre-wrap text-xs text-muted", details.message));
    details.pages.forEach((page) => box.append(pageSection(page)));
    if (details.other_files.length) {
        box.append(element("p", "text-xs text-muted [overflow-wrap:anywhere]",
            `Autres fichiers modifiés : ${details.other_files.join(", ")}`));
    }
    if (!details.pages.length && !details.other_files.length) box.append(element("p", "text-muted", "Aucun fichier modifié."));
    return box;
}
