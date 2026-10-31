// MyCMS - page de connexion (et création des identifiants au premier lancement)
// Module autonome : la page est accessible sans être connecté, sans les autres scripts de l'interface

const $ = (id) => document.getElementById(id);
const login = { setupNeeded: false };

function showError(message) {
    $("auth-error").textContent = message;
    $("auth-error").classList.toggle("hidden", !message);
}

async function post(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) throw new Error(data.error || `Erreur HTTP ${response.status}`);
    return data;
}

$("auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");
    const body = { username: $("username").value, password: $("password").value };
    $("auth-submit").disabled = true;
    try {
        if (login.setupNeeded) {
            await post("/api/auth/setup", { ...body, confirm: $("confirm").value });
        } else {
            await post("/api/auth/login", body);
        }
        location.replace("/" + location.hash);
    } catch (err) {
        showError(err.message);
        $("password").select();
    } finally {
        $("auth-submit").disabled = false;
    }
});

async function start() {
    try {
        const state = await (await fetch("/api/auth/state")).json();
        if (state.logged_in) return location.replace("/" + location.hash);
        login.setupNeeded = state.setup_needed;
    } catch {
        showError("Le serveur MyCMS ne répond pas");
    }
    if (login.setupNeeded) {
        document.title = "MyCMS - Création des identifiants";
        $("auth-intro").textContent = "Premier lancement : créez le compte administrateur, avec un identifiant et un mot de passe (8 caractères minimum). Notez-les bien. Vous pourrez ensuite créer un compte pour chaque personne dans les Paramètres.";
        $("password").autocomplete = "new-password";
        $("confirm-row").classList.replace("hidden", "flex");
        $("confirm").required = true;
        $("auth-submit").textContent = "Créer le compte administrateur";
    }
    $("username").focus();
}

start();
