// MyCMS - utilitaires : éléments de la page, appels à l'API, messages

export const $ = (id) => document.getElementById(id);

export async function api(method, url, body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if (response.status === 401) {
        // Session expirée ou fermée : retour à la page de connexion
        location.replace("/login");
        throw new Error("Session expirée : reconnectez-vous");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) {
        const error = new Error(data.error || data.message || data.output || `Erreur HTTP ${response.status}`);
        error.data = data;
        throw error;
    }
    return data;
}

export function toast(message, isError = false) {
    const el = document.createElement("div");
    el.className = isError ? "toast error" : "toast";
    el.textContent = message;
    $("toasts").appendChild(el);
    setTimeout(() => el.remove(), isError ? 8000 : 4000);
}

// Désactive le bouton pendant l'action et affiche le résultat ou l'erreur
export async function withButton(button, action) {
    button.disabled = true;
    button.classList.add("busy");
    try {
        await action();
    } catch (e) {
        toast(e.message, true);
    } finally {
        button.disabled = false;
        button.classList.remove("busy");
    }
}

export function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
}

export function plural(count, word, words = `${word}s`) {
    return `${count} ${count > 1 ? words : word}`;
}
