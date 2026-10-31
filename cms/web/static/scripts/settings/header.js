// MyCMS - en-tête : guide d'utilisation et déconnexion

import { $, api, toast } from "../core/dom.js";
import { dirtyCount, warnUnsaved } from "../editor/editor.js";
import { state } from "../core/state.js";

export function openGuide() {
    $("guide-at-startup").checked = state.config.show_guide !== false;
    if (!$("guide-dialog").open) $("guide-dialog").showModal();
}

export function initHeader() {
    $("open-guide").addEventListener("click", openGuide);
    $("guide-close").addEventListener("click", () => $("guide-dialog").close());

    $("guide-at-startup").addEventListener("change", (e) => {
        api("POST", "/api/config", { show_guide: e.target.checked })
            .then((result) => { state.config = result.config; })
            .catch((err) => toast(err.message, true));
    });

    $("logout").addEventListener("click", async () => {
        if (dirtyCount() && !confirm("Des modifications non sauvegardées seront perdues. Se déconnecter ?")) return;
        await api("POST", "/api/auth/logout").catch(() => {});
        window.removeEventListener("beforeunload", warnUnsaved);
        location.replace("/login");
    });
}
