// MyCMS - publication plus sûre : vérification avant d'envoyer, suivi de la mise en ligne, conflits

import { $, api, element, plural, toast, withButton } from "../core/dom.js";

const POLL_MS = 10000;
const MAX_WAIT_MS = 10 * 60 * 1000;
// Suivi de la mise en ligne en cours
const online = { timer: null, started: 0 };

export function formatProblems(problems) {
    return problems.map((p) => `• ${p.page}, ligne ${p.line} : ${p.message}`).join("\n");
}

const found = (count) => plural(count, "problème trouvé", "problèmes trouvés");

// Encadré sous les boutons : rouge avec la liste des problèmes, vert s'il n'y en a pas
export function showCheckResults(title, problems, okText) {
    const box = $("check-results");
    box.className = problems.length ? "check-results error" : "check-results ok";
    if (!problems.length) {
        box.replaceChildren(element("p", "font-semibold", okText));
        return;
    }
    const list = element("ul", "flex list-disc flex-col gap-0.5 pl-5");
    problems.forEach((p) => list.append(element("li", "[overflow-wrap:anywhere]",
        `${p.page}, ligne ${p.line} : ${p.message}`)));
    box.replaceChildren(element("p", "font-semibold", `${title} : ${found(problems.length)}`), list,
        element("p", "text-xs", "Ces erreurs sont dans le code des pages (liens vers des fichiers absents, adresses "
            + "mal écrites, sites qui ont changé d'adresse…). Si vous ne savez pas les corriger, transmettez cette "
            + "liste à un développeur."));
}

// Avant un push : problèmes des pages pas encore publiées. Retourne faux si l'utilisateur préfère corriger
export async function confirmPublication() {
    const { problems } = await api("GET", "/api/checks");
    if (!problems.length) return true;
    showCheckResults("Avant la publication", problems);
    return confirm(`${found(problems.length)} dans les pages à publier (liste dans l'onglet Git) :\n\n`
        + `${formatProblems(problems.slice(0, 8))}\n\nPublier quand même ?`);
}

function showOnline(text) {
    $("online-status").textContent = text;
    $("online-status").classList.toggle("hidden", !text);
}

async function pollOnline(pages) {
    let status;
    try {
        status = await api("GET", `/api/online?${pages.map((p) => `page=${encodeURIComponent(p)}`).join("&")}`);
    } catch (e) {
        showOnline(`Suivi de la mise en ligne impossible : ${e.message}`);
        return;
    }
    if (!status.waiting.length) {
        showOnline(`✓ En ligne sur ${status.base_url} (${plural(status.online.length, "page")})`);
        toast("Votre modification est en ligne.");
        return;
    }
    if (Date.now() - online.started > MAX_WAIT_MS) {
        showOnline(`La mise en ligne prend plus de temps que prévu (${status.waiting.join(", ")}). `
            + "Rechargez le site dans quelques minutes.");
        return;
    }
    showOnline(`⏳ Mise en ligne en cours : ${status.online.length} / ${pages.length} page(s) à jour…`);
    online.timer = setTimeout(() => pollOnline(pages), POLL_MS);
}

// Après un push réussi : vérifier toutes les 10 secondes que le site en ligne a les nouvelles pages
export function watchOnline(pages) {
    clearTimeout(online.timer);
    if (!pages?.length) {
        showOnline("");
        return;
    }
    online.started = Date.now();
    showOnline("⏳ Mise en ligne en cours (une à deux minutes)…");
    online.timer = setTimeout(() => pollOnline(pages), POLL_MS);
}

// Conflit au pull ou au push : proposer de reprendre la version en ligne
export function showConflict(isConflict) {
    $("git-reset-remote").classList.toggle("hidden", !isConflict);
}

// Appelée par initGit : boutons « Vérifier le site » et « Reprendre la version en ligne »
export function bindPublishChecks({ afterReset }) {
    $("git-check").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const external = $("git-check-external")?.checked;
        if (external) toast("Vérification des liens externes : quelques secondes…");
        const { pages, problems } = await api("GET", `/api/checks?scope=all${external ? "&external=1" : ""}`);
        showCheckResults("Vérification du site", problems,
            `✓ Aucun problème trouvé (${plural(pages.length, "page vérifiée", "pages vérifiées")}).`);
        if (problems.length) toast(`${found(problems.length)} : la liste est sous les boutons de l'onglet Git.`, true);
        else toast("Aucun problème trouvé");
    }));

    $("git-reset-remote").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (!confirm("Vos modifications et commits pas encore publiés seront définitivement perdus, "
            + "et les fichiers reprendront leur version en ligne. Continuer ?")) return;
        toast((await api("POST", "/api/git/reset-to-remote")).message);
        showConflict(false);
        await afterReset();
    }));
}
