// MyCMS - Paramètres : « Mon compte », nom et e-mail qui signent les publications

import { $, api, toast, withButton } from "../core/dom.js";
import { onTabOpen } from "../core/tabs.js";

async function loadProfile() {
    const profile = await api("GET", "/api/auth/profile");
    $("account-name").value = profile.name;
    $("account-email").value = profile.email;
    $("account-author").textContent = `Vos publications sont signées : ${profile.author}`;
}

export function initAccount() {
    onTabOpen("settings", () => loadProfile().catch((e) => toast(e.message, true)));

    $("account-save").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const result = await api("POST", "/api/auth/profile", {
            name: $("account-name").value,
            email: $("account-email").value,
        });
        toast(result.message);
        await loadProfile();
    }));
}
