// MyCMS - onglet Git : repository, clone, statut, pull, push, messages de commit préfaits

import { $, api, toast, withButton } from "../core/dom.js";
import { loadFiles, refreshPublished } from "../editor/editor.js";
import { refreshBranches } from "./branches.js";
import { refreshHistory } from "./history.js";
import { bindPublishChecks, confirmPublication, showConflict, watchOnline } from "./publish-checks.js";
import { loadConfig } from "../settings/settings.js";
import { state } from "../core/state.js";
import { onTabOpen } from "../core/tabs.js";

// Dossier choisi sans .git : proposer de récupérer le site, dans ce dossier par défaut
const clone = { prefill: "" };

function showGitOutput(text) {
    $("git-output").textContent = text;
}

function showCloneCard(hasGit) {
    $("clone-card").classList.toggle("hidden", hasGit);
    const input = $("clone-path");
    if (!hasGit && (!input.value || input.value === clone.prefill)) {
        input.value = clone.prefill = state.config.repo_path || "";
    }
}

export async function refreshGitStatus() {
    let status;
    try {
        status = await api("GET", "/api/git/status");
    } catch (e) {
        status = { ...e.data, output: e.message };
    }
    showGitOutput(status.output);
    showCloneCard(status.has_git !== false);
    await refreshBranches();
    await refreshHistory();
}

// Le chemin saisi devient le repository courant
export async function useRepoPath() {
    await api("POST", "/api/config", { repo_path: $("git-repo").value.trim() });
    await loadConfig();
    try {
        toast((await api("POST", "/api/git/verify")).message);
    } finally {
        await loadFiles();
        await refreshGitStatus();
    }
}

// Messages de commit préfaits : remplissent le champ, le message reste modifiable
function updateCommitPresets() {
    const message = $("commit-message").value.trim();
    document.querySelectorAll("#commit-presets button").forEach((b) => {
        b.setAttribute("aria-pressed", String(b.textContent === message));
    });
}

function initCommitPresets() {
    document.querySelectorAll("#commit-presets button").forEach((button) => {
        button.addEventListener("click", () => {
            const input = $("commit-message");
            input.value = button.textContent;
            input.focus();
            input.setSelectionRange(input.value.length, input.value.length);
            updateCommitPresets();
        });
    });
    $("commit-message").addEventListener("input", updateCommitPresets);
    updateCommitPresets();
}

// Une action Git, puis le statut (et la version publiée, qui peut avoir changé) mis à jour.
// before : vérification préalable (faux : action abandonnée) ; after : suite donnée au résultat
function gitAction(id, url, { body, published = false, before, after } = {}) {
    $(id).addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (before && !(await before())) return;
        try {
            const result = await api("POST", url, body?.());
            showConflict(false);
            toast(result.message);
            after?.(result);
        } catch (err) {
            showConflict(Boolean(err.data?.conflict));
            throw err;
        } finally {
            await refreshGitStatus();
            if (published) await refreshPublished().catch(() => {});
        }
    }));
}

function onPublishedBranch() {
    const { current, published } = state.branch;
    return !published || current === published;
}

export function initGit() {
    onTabOpen("git", refreshGitStatus);
    $("git-verify").addEventListener("click", (e) => withButton(e.currentTarget, useRepoPath));

    $("git-clone").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const url = $("clone-url").value.trim();
        if (!url) throw new Error("Veuillez entrer l'adresse du repository");
        showGitOutput("Récupération du site en cours…");
        try {
            const result = await api("POST", "/api/git/clone", { url, path: $("clone-path").value.trim() });
            toast(result.message);
            $("clone-url").value = "";
            $("clone-path").value = "";
            await loadConfig();
            await loadFiles();
        } finally {
            await refreshGitStatus();
        }
    }));

    initCommitPresets();
    gitAction("git-pull", "/api/git/pull", { published: true });
    gitAction("git-push", "/api/git/push", {
        body: () => ({ message: $("commit-message").value }),
        published: true,
        before: confirmPublication,
        // Sur une autre branche que la branche publiée, le site en ligne ne change pas : rien à suivre
        after: (result) => watchOnline(onPublishedBranch() ? result.pages : []),
    });
    gitAction("git-add", "/api/git/add");
    $("git-status").addEventListener("click", (e) => withButton(e.currentTarget, refreshGitStatus));
    bindPublishChecks({
        afterReset: async () => {
            await refreshGitStatus();
            await loadFiles();
            await refreshPublished().catch(() => {});
        },
    });
}
