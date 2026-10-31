// MyCMS - Paramètres : comptes des utilisateurs (administrateurs seulement)

import { $, api, element, toast, withButton } from "../core/dom.js";
import { state } from "../core/state.js";
import { onTabOpen } from "../core/tabs.js";

const NEW_USER_FIELDS = ["user-new-name", "user-new-password", "user-new-confirm"];

// Nouveau mot de passe d'un compte : formulaire affiché dans sa ligne
function resetForm(user) {
    const form = element("div", "hidden w-full flex-wrap items-center gap-2");
    const input = element("input", "input max-w-xs flex-1");
    input.type = "password";
    input.autocomplete = "new-password";
    input.placeholder = "Nouveau mot de passe";
    input.setAttribute("aria-label", `Nouveau mot de passe de ${user.username}`);
    const save = element("button", "btn", "Valider");
    save.addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const result = await api("POST", `/api/users/${encodeURIComponent(user.username)}/password`,
            { password: input.value });
        toast(result.message);
        renderUsers(result.users);
    }));
    form.append(input, save);
    return form;
}

function userRow(user) {
    const isMe = user.username === state.user.name;
    const row = element("li", "flex flex-wrap items-center gap-2 rounded-lg border border-line px-3 py-2");
    const name = element("span", "font-semibold", user.username);
    const label = user.owner ? "Administrateur principal" : user.admin ? "Administrateur" : "Éditeur";
    const role = element("span", user.admin ? "badge-on" : "rounded-full bg-surface-2 px-2.5 py-1 text-xs", label);
    row.append(name, role);
    if (isMe) row.append(element("span", "text-muted", "(vous)"));

    // Administrateur principal (le premier compte) : ses accès ne peuvent pas lui être retirés
    if (user.owner) {
        row.title = "Premier compte créé : il ne peut être ni rétrogradé ni supprimé";
        return row;
    }

    const actions = element("div", "ml-auto flex flex-wrap gap-2");
    const toggle = element("button", "btn px-2.5 py-1 text-xs", user.admin ? "Rendre éditeur" : "Rendre administrateur");
    toggle.addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        if (isMe && !confirm("Vous ne pourrez plus gérer les comptes. Continuer ?")) return;
        const result = await api("POST", `/api/users/${encodeURIComponent(user.username)}/role`, { admin: !user.admin });
        toast(result.message);
        if (isMe) return location.reload();
        renderUsers(result.users);
    }));
    actions.append(toggle);

    if (!isMe) {
        const form = resetForm(user);
        const reset = element("button", "btn px-2.5 py-1 text-xs", "Nouveau mot de passe");
        reset.addEventListener("click", () => {
            form.classList.toggle("hidden");
            form.classList.toggle("flex");
            form.querySelector("input").focus();
        });
        const remove = element("button", "btn btn-danger px-2.5 py-1 text-xs", "Supprimer");
        remove.addEventListener("click", (e) => withButton(e.currentTarget, async () => {
            if (!confirm(`Supprimer le compte « ${user.username} » ?`)) return;
            const result = await api("DELETE", `/api/users/${encodeURIComponent(user.username)}`);
            toast(result.message);
            renderUsers(result.users);
        }));
        actions.append(reset, remove);
        row.append(actions, form);
    } else {
        row.append(actions);
    }
    return row;
}

function renderUsers(users) {
    $("users-list").replaceChildren(...users.map(userRow));
}

async function refreshUsers() {
    if (!state.user.admin) return;
    renderUsers((await api("GET", "/api/users")).users);
}

export function initUsers() {
    onTabOpen("settings", () => refreshUsers().catch((e) => toast(e.message, true)));

    $("user-add").addEventListener("click", (e) => withButton(e.currentTarget, async () => {
        const result = await api("POST", "/api/users", {
            username: $("user-new-name").value,
            password: $("user-new-password").value,
            confirm: $("user-new-confirm").value,
            admin: $("user-new-admin").checked,
        });
        NEW_USER_FIELDS.forEach((id) => { $(id).value = ""; });
        $("user-new-admin").checked = false;
        toast(result.message);
        renderUsers(result.users);
    }));
}

// Compte connecté : affiché dans l'en-tête, carte Utilisateurs pour les administrateurs
export async function loadUser() {
    const auth = await api("GET", "/api/auth/state");
    state.user = { name: auth.username || "", admin: Boolean(auth.admin) };
    $("user-name").textContent = state.user.name;
    $("user-name").title = state.user.admin ? "Administrateur" : "Éditeur";
    $("users-card").classList.toggle("hidden", !state.user.admin);
}
