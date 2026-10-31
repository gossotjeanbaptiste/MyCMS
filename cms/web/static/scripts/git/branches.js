// MyCMS - onglet Git : branches du site (créer, changer, fusionner, supprimer)

import { $, api, toast, withButton } from "../core/dom.js";
import { state } from "../core/state.js";
import { dirtyCount, loadFiles, refreshPublished } from "../editor/editor.js";
import { refreshGitStatus } from "./git.js";

function describe(branch) {
    const where = branch.local && branch.remote ? "" : branch.local ? " · cet ordinateur seulement" : " · GitHub seulement";
    const tags = [branch.current && "actuelle", branch.published && "publiée"].filter(Boolean);
    return `${branch.name}${tags.length ? ` (${tags.join(", ")})` : ""}${where}`;
}

function render(data) {
    state.branch = { current: data.current, published: data.published };
    $("branches-card").classList.remove("hidden");
    const published = data.published ? `Branche publiée : ${data.published} (celle du site en ligne).`
        : "Branche publiée inconnue (pas encore de GitHub).";
    const draft = data.published && data.current !== data.published ? " Vos push ne changent pas le site en ligne." : "";
    $("branch-current").textContent = `Branche actuelle : ${data.current}. ${published}${draft}`;
    const select = $("branch-select");
    const chosen = select.value;
    select.replaceChildren(...data.branches.map((b) => new Option(describe(b), b.name)));
    // Par défaut : une autre branche que l'actuelle (la publiée si possible), pour changer ou fusionner
    const others = data.branches.filter((b) => !b.current);
    const fallback = others.find((b) => b.published) || others[0] || data.branches[0];
    select.value = data.branches.some((b) => b.name === chosen && !b.current) ? chosen : fallback?.name || "";
}

export async function refreshBranches({ fetch = false } = {}) {
    try {
        const data = await api("GET", `/api/git/branches${fetch ? "?fetch=1" : ""}`);
        render(data);
        if (data.message) toast(data.message, data.message.startsWith("✗"));
    } catch {
        state.branch = { current: "", published: "" };
        $("branches-card").classList.add("hidden"); // Pas de repository Git
    }
}

// La branche a changé : l'éditeur montre les pages de la nouvelle branche
async function afterChange() {
    const files = await loadFiles();
    if (files.includes(state.editor.file)) await refreshPublished();
    await refreshGitStatus();
}

async function act(action, name, extra = {}) {
    try {
        const result = await api("POST", "/api/git/branches", { action, name, ...extra });
        toast(result.message);
        render(result);
    } catch (err) {
        if (err.data?.unmerged && confirm(`${err.message}\n\nSupprimer quand même ?`)) {
            return act(action, name, { ...extra, force: true });
        }
        throw err;
    }
    await afterChange();
}

function editorSaved() {
    if (!dirtyCount()) return true;
    toast("Sauvegardez ou annulez d'abord les modifications de l'éditeur.", true);
    return false;
}

function bind(id, action) {
    $(id).addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const name = $("branch-select").value;
        if (!name) return;
        if (action === "switch" && !editorSaved()) return;
        if (action === "merge" && (!editorSaved() || !confirm(
            `Fusionner « ${name} » dans « ${state.branch.current} » ? Ses modifications seront ajoutées à la branche actuelle.`))) return;
        const remote = action === "delete" && $("branch-delete-remote").checked;
        const where = remote ? "de cet ordinateur et de GitHub (pour tout le monde)" : "de cet ordinateur";
        if (action === "delete" && !confirm(`Supprimer la branche « ${name} » ${where} ?`)) return;
        await act(action, name, remote ? { remote } : {});
    }));
}

export function initBranches() {
    bind("branch-switch", "switch");
    bind("branch-merge", "merge");
    bind("branch-delete", "delete");
    $("branch-create").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const name = $("branch-name").value.trim();
        if (!name) throw new Error("Veuillez indiquer le nom de la nouvelle branche");
        await act("create", name);
        $("branch-name").value = "";
    }));
    $("branch-fetch").addEventListener("click", (e) => withButton(e.currentTarget, () => refreshBranches({ fetch: true })));
}
