// MyCMS - onglet Paramètres : configuration, sitemap, mot de passe (les comptes sont dans users.js)

import { $, api, toast, withButton } from "../core/dom.js";
import { loadFiles } from "../editor/editor.js";
import { state } from "../core/state.js";
import { onTabOpen } from "../core/tabs.js";

export async function loadConfig() {
    const config = await api("GET", "/api/config");
    state.config = config;
    $("git-repo").value = config.repo_path;
    $("set-repo").value = config.repo_path;
    $("set-port").value = config.default_port;
    $("set-site-url").value = config.site_url || "";
    $("set-auto-pull").checked = config.auto_pull;
    if (!state.preview.running) $("preview-port").value = config.default_port;
}

async function refreshSitemapInfo() {
    const info = await api("GET", "/api/sitemap");
    const location = info.location ? `Emplacement : ${info.location}` : "Aucun sitemap : il sera créé à la racine";
    const url = info.base_url ? `URL du site : ${info.base_url}` : "URL du site introuvable : renseignez-la ci-dessus";
    $("sitemap-info").textContent = `${location} · ${url}`;
}

export function initSettings() {
    onTabOpen("settings", () => refreshSitemapInfo().catch((e) => toast(e.message, true)));

    $("settings-save").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        await api("POST", "/api/config", {
            repo_path: $("set-repo").value.trim(),
            site_url: $("set-site-url").value.trim(),
            default_port: Number($("set-port").value),
            auto_pull: $("set-auto-pull").checked,
        });
        await loadConfig();
        await loadFiles();
        await refreshSitemapInfo();
        toast("Paramètres sauvegardés");
    }));

    $("sitemap-generate").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        toast((await api("POST", "/api/sitemap")).message);
        await refreshSitemapInfo();
    }));

    $("pw-save").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const result = await api("POST", "/api/auth/password", {
            current: $("pw-current").value,
            new: $("pw-new").value,
            confirm: $("pw-confirm").value,
        });
        ["pw-current", "pw-new", "pw-confirm"].forEach((id) => { $(id).value = ""; });
        toast(result.message);
    }));

    $("settings-reset").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (!confirm("Réinitialiser tous les paramètres ?")) return;
        await api("POST", "/api/config/reset");
        await loadConfig();
        await loadFiles();
        toast("Paramètres réinitialisés");
    }));
}
