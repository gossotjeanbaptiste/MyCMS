// MyCMS - onglet Git : repository, clone, statut, pull, push, messages de commit préfaits

import { $, api, toast, withButton } from "../core/dom.js";
import { loadFiles, refreshPublished } from "../editor/editor.js";
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

// Une action Git, puis le statut (et la version publiée, qui peut avoir changé) mis à jour
function gitAction(id, url, { body, published = false } = {}) {
    $(id).addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        try {
            toast((await api("POST", url, body?.())).message);
        } finally {
            await refreshGitStatus();
            if (published) await refreshPublished().catch(() => {});
        }
    }));
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
    gitAction("git-push", "/api/git/push", { body: () => ({ message: $("commit-message").value }), published: true });
    gitAction("git-add", "/api/git/add");
    $("git-status").addEventListener("click", (e) => withButton(e.currentTarget, refreshGitStatus));
}
